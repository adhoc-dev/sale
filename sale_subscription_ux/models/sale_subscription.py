##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class SaleSubscription(models.Model):

    _inherit = "sale.subscription"

    dates_required = fields.Boolean(
        related="template_id.dates_required",
        readonly=True,
    )

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        # esto lo hacemos porque suele ser utili poder buscar por cuenta
        # anallitica
        args = args or []
        domain = [
            '|', '|', ('analytic_account_id', operator, name),
            ('code', operator, name), ('name', operator, name)]
        partners = self.env['res.partner'].search([('name', operator, name)], limit=limit)
        if partners:
            domain = ['|'] + domain + [('partner_id', 'in', partners.ids)]
        rec = self.search(domain + args, limit=limit)
        return rec.name_get()

    @api.multi
    def _prepare_invoice_data(self):
        """ Copy the terms and conditions of the subscription as part of the
        invoice note.
        """
        self.ensure_one()
        res = super(SaleSubscription, self)._prepare_invoice_data()
        if self.template_id.copy_description_to_invoice:
            res.update({'comment':res.get('comment', '') + '\n\n' + (
                self.description or '')})
        return res

    @api.multi
    def update_lines_prices_from_products(self):
        """ Update subscription lines, all the line including prices.
        """
        for subscription in self:
            for line in subscription.recurring_invoice_line_ids:
                line.onchange_product_quantity()
        self._compute_recurring_total()

    def _prepare_invoice(self):
        """ Improove prepare invoice to use _set_additional_fields method
        """
        vals = super(SaleSubscription, self)._prepare_invoice()
        temp_invoice = self.env['account.invoice'].new(vals)
        new_lines = []
        for temp_line in temp_invoice.invoice_line_ids:
            temp_line._set_additional_fields(temp_invoice)
            new_lines.append(
                (0, 0, temp_line._convert_to_write(temp_line._cache)))
        vals['invoice_line_ids'] = new_lines
        return vals

    def prepare_renewal_order(self):
        # Set default company as the same in the subscription
        return super(SaleSubscription, self.with_context(
            default_company_id=self.company_id.id)).prepare_renewal_order()
