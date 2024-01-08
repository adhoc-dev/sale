from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    index = fields.Float('Index', compute="_compute_index")
    gathering_balance_indexed = fields.Float(
        compute="_compute_gathering_balance_indexed",
        digits='Product Price',
    )

    @api.depends('order_line.product_template_id.list_price')
    def _compute_index(self):
        for order in self:
            if order.is_gathering:
                order_lines_gathered = order.order_line.filtered(lambda x: x.initial_qty_gathered > 0)

                if not order_lines_gathered:
                    order.index = 0.0
                    continue

                qty = sum(order_lines_gathered.mapped('initial_qty_gathered'))

                index = sum(
                    (line.product_template_id.list_price - line.price_unit) / line.price_unit * (line.initial_qty_gathered / qty)
                    for line in order_lines_gathered
                )

                order.index = index
            else:
                order.index = 0.0

    @api.depends('gathering_balance', 'index')
    def _compute_gathering_balance_indexed(self):
        self.gathering_balance_indexed = self.gathering_balance * (self.index + 1)
