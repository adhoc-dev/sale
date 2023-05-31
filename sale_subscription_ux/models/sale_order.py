##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api
from markupsafe import Markup
from odoo.tools import is_html_empty


class SaleOrder(models.Model):

    _inherit = "sale.order"

    dates_required = fields.Boolean(
        related="sale_order_template_id.dates_required",
    )

    def update_lines_prices_from_products(self):
        """ Update subscription lines, all the line including prices.
        """
        for subscription in self:
            for line in subscription.order_line:
                price = line.with_company(line.company_id)._get_display_price()
                line.price_unit = line.product_id._get_tax_included_unit_price(
                    line.company_id,
                    line.order_id.currency_id,
                    line.order_id.date_order,
                    'sale',
                    fiscal_position=line.order_id.fiscal_position_id,
                    product_price_unit=price,
                    product_currency=line.currency_id
                )

    # Este fix surge de un problema que reporta adhoc al querer editar las cantidades de una línea de una suscripción.
    # TODO revisar
    def _create_upsell_activity(self):
        if self.id:
            super()._create_upsell_activity()

    def _handle_automatic_invoices(self, auto_commit, invoices):
        # Modificamos para permitir el posteo o no según corresponda
        auto_post_orders = self.filtered(
            lambda x: not x.sale_order_template_id or
              x.sale_order_template_id.invoicing_method == 'autopost' or
              x.payment_token_id
            )
        without_auto_post_orders = self - auto_post_orders
        # Sacamos las facturas que no tienen autopost para que no corra el _handle_automatic_invoice y queden en borrador
        for order in without_auto_post_orders:
            invoice = invoices.filtered(lambda inv: inv.invoice_origin == order.name)
            if invoice.move_type == 'out_invoice' and invoice.partner_id:
                # Las facturas que se crean en borrador cuyo partner tiene direct debit mandate tengan asignado
                # dicho mandate en la factura, para que al validarla manualmente se genere el recibo correspondiente
                mandate = self.env['account.direct_debit.mandate'].search([
                    ('partner_id.commercial_partner_id', '=', invoice.partner_id.commercial_partner_id.id),
                    ('state', '=', 'active')], limit=1)
                invoice.direct_debit_mandate_id = mandate
            invoices -= invoice
        return super(SaleOrder, auto_post_orders)._handle_automatic_invoices(auto_commit, invoices)


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        if self.order_id.is_subscription and not self.order_id.sale_order_template_id.add_period_dates_to_description:
            product_desc = self.product_id.get_product_multiline_description_sale() + self._get_sale_order_line_multiline_description_variants()
            res.update({
                'name': product_desc,
            })
        return res
