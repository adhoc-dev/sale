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
