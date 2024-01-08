from odoo import models, api, _
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model_create_multi
    def create(self, vals_list):
        order_id = vals_list[0].get('order_id') if vals_list else False
        if (
            order_id
            and self.env['sale.order'].browse(order_id).is_gathering
            and self.env['sale.order'].browse(order_id).state == 'sale'
        ):
            existing_product_ids = set(self.env['sale.order.line'].search([
                ('order_id', '=', order_id),
                ('initial_qty_gathered', '>', 0)
            ]).mapped('product_template_id.id'))
            new_product_ids = set(vals.get('product_template_id') for vals in vals_list)
            if existing_product_ids.intersection(new_product_ids):
                raise UserError(_("You can't add an already gathered product more than once. Please modify the quantity of the existing line."))
            lines = super(SaleOrderLine, self).create(vals_list)
            for line in lines:
                line._update_line_for_gathering()
            return lines
        else:
            return super(SaleOrderLine, self).create(vals_list)

    def write(self, vals):
        if (
            self.order_id.is_gathering
            and self.order_id.state == 'sale'
            and 'product_uom_qty' in vals
            and vals['product_uom_qty'] > self.product_uom_qty
            and 'initial_qty_gathered' not in vals
            and self.initial_qty_gathered == 0
        ):
            raise UserError(_("You can't modify the quantity of an added product. Please add a new line."))
        return super(SaleOrderLine, self).write(vals)

    def _update_line_for_gathering(self):
        if (
            self.order_id.is_gathering and self.order_id.state == 'sale'
            and self.display_type not in ['line_section', 'line_note']
        ):
            self.price_unit /= (1 + self.order_id.index)
            self.name += f' ({str(round(self.order_id.index*100, 2))}%) (${str(round(self.product_template_id.list_price, 2))})'
