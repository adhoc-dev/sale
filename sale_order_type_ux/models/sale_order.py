##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    type_id = fields.Many2one(
        tracking=True,
    )

    @api.depends("partner_shipping_id", "partner_id", "company_id", "type_id")
    def _compute_fiscal_position_id(self):
        """The order type wins, but only with a position the order's company can use.

        Two things were wrong with taking ``type_id.fiscal_position_id`` unconditionally.
        It did not iterate, so on a recordset of more than one order the value of whichever
        types happened to be in it was written to all of them. And, the reason this is being
        fixed: it ignored the company, so changing the company of an order whose type
        carries a position left the position of the old company in place — the field is
        ``check_company=True``, so what looks like "it did not recompute" is a value that
        does not belong in the new company at all.

        A position is usable by a company when it is global or owned by one of its
        ancestors, which is ``check_company_domain_parent_of``, the domain the field itself
        is checked against. When the type's position is not usable, the standard detection
        for the new company answers instead.
        """
        typed = self.env["sale.order"]
        for order in self:
            fpos = order.type_id.fiscal_position_id
            if fpos and (not fpos.company_id or fpos.company_id in order.company_id.parent_ids):
                if order.fiscal_position_id != fpos and order.order_line:
                    # Same flag core raises: the taxes of the lines do not follow the
                    # position on their own, so the "Update Taxes" button has to show up.
                    order.show_update_fpos = True
                order.fiscal_position_id = fpos
                typed |= order
        return super(SaleOrder, self - typed)._compute_fiscal_position_id()

    @api.model_create_multi
    def create(self, vals):
        res = super().create(vals)
        if res.type_id and self.env.context.get("website_id"):
            res._compute_fiscal_position_id()
        return res

    @api.onchange("type_id")
    def _onchange_team_id(self):
        if self.type_id and self.type_id.team_id:
            self.team_id = self.type_id.team_id

    def _create_invoices(self, grouped=False, final=False, date=None):
        """
        Overrides the `_create_invoices` method to ensure that taxes are correctly computed
        for the company of the invoice. In cases where the company has a localization
        (e.g., l10n_ar), this ensures that the taxes from `l10n_ar_tax_ids` are applied.
        Also creates separate invoices for each sale order type when multiple types are present.
        """
        # If we have multiple order types and not explicitly grouped, create separate invoices per type
        if len(self.mapped("type_id")) > 1 and not grouped:
            all_invoices = self.env["account.move"]
            for order_type in self.mapped("type_id"):
                orders_with_type = self.filtered(lambda x: x.type_id.id == order_type.id)
                type_invoices = super(SaleOrder, orders_with_type)._create_invoices(
                    grouped=grouped, final=final, date=date
                )
                all_invoices |= type_invoices
            invoices = all_invoices
        else:
            invoices = super()._create_invoices(grouped=grouped, final=final, date=date)

        return invoices

    def _get_protected_fields(self):
        return super()._get_protected_fields() + ["type_id"]

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        if self.type_id.invoice_company_id and self.type_id.invoice_company_id != self.company_id:
            res["company_id"] = self.type_id.invoice_company_id.id
        return res
