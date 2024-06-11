from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    initial_qty_gathered = fields.Float(string='Initial Quantity Gathered', copy=False)

    @api.depends('initial_qty_gathered', 'order_id.is_gathering')
    def _compute_price_unit(self):
        gathering_lines = self.filtered(lambda x: x.order_id.is_gathering and x.initial_qty_gathered > 0)
        super(SaleOrderLine, self - gathering_lines)._compute_price_unit()

    def _prepare_invoice_line(self, **optional_values):
        result = super()._prepare_invoice_line(**optional_values)
        if self.is_downpayment and self._context.get(
                'invoice_gathering', False):
            lines = self.order_id.order_line.filtered(
                lambda x: not x.is_downpayment and x.qty_to_invoice)
            price_subtotal = lines and sum(lines.mapped(
                lambda l: l.qty_to_invoice * l.price_unit)) or 0.0
            result['price_unit'] = self.tax_id.compute_all(
                price_subtotal, currency=self.order_id.currency_id)[
                'total_excluded']
            result['quantity'] = -1.0
        return result

    def write(self, vals):
        if "discount" in vals:
            if self.filtered(lambda x: x.order_id.is_gathering and x.order_id.state == 'sale' and x.initial_qty_gathered > 0):
                raise UserError(_("You cannot modify the discount of the gathering lines once the sale has been confirmed.\n"))
        return super().write(vals)

    @api.constrains('discount')
    def _check_discount(self):
        for rec in self.filtered(lambda x: x.order_id.is_gathering and x.state == 'sale' and x.initial_qty_gathered == 0 and x.discount > 0):
            raise ValidationError(_("Cannot add discounts to redeemed products."))
