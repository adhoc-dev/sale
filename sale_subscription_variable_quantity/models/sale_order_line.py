##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api
from odoo.tools import float_is_zero
from odoo.tools.safe_eval import safe_eval


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    quantity_formula_id = fields.Many2one(
        'sale.order.line.quantity.formula', string='Qty Formula', help='If you set a quantity formula, then when '
        'creating the recurring invoice the quantity will be calculated by this formula and quantity field will be '
        'ignored')

    def _prepare_invoice_line(self, **optional_values):
        """ Para implementar cantidades segun formula vimos estas opciones:
        a) actualizar las lineas de la ov antes de mandar a facturar actualizando qty_delivered o product_uom_qty segun
        el tipo de producto para que luego el metodo "_get_subscription_qty_to_invoice" calcula la cantidad
        correspondiente.
        b) extender directamente el método "_get_subscription_qty_to_invoice" para implementar un nuevo caso
        De las opciones anteriores "a" pareció ser mas limpia, pero ambas opciones nos limitan a solo poder manipular la
        cantidad y, al menos en nuestro caso, queremos también poder modificar, por ejemplo, la distribución analítica.
        Por esa razón vamos directamente en este método que nos da más flexibilidad.
        Se puede ver commit anterior donde borramos las herencias de approaches a y b
        """
        self.ensure_one()
        res = super()._prepare_invoice_line(**optional_values)
        if self.order_id.is_subscription and self.quantity_formula_id:
            res.update(self.quantity_formula_id._get_result(self))
        return res

    # def _reset_subscription_qty_to_invoice(self):
    #     """ Antes de que se cree factura actualizamos las cantidades de los poductos por formula asi 
    #     """
    #     import pdb; pdb.set_trace()
    #     formula_lines = self.filtered('quantity_formula_id')
    #     # super(SaleOrderLine, self - formula_lines)._reset_subscription_qty_to_invoice()
    #     for line in formula_lines:
    #         if line.product_id.invoice_policy == 'order':
    #             line.product_uom_qty = 100.0
    #         else:
    #             line.qty_delivered = 100.0
    #     return super(SaleOrderLine, self)._reset_subscription_qty_to_invoice()

    # def _get_subscription_qty_to_invoice(self, last_invoice_date=False, next_invoice_date=False):
    #     formula_lines = self.filtered('quantity_formula_id')
    #     result = super(SaleOrderLine, self - formula_lines)._get_subscription_qty_to_invoice(
    #         last_invoice_date=last_invoice_date, next_invoice_date=next_invoice_date)
    #     # result = {}
    #     qty_invoiced = formula_lines._get_subscription_qty_invoiced(last_invoice_date, next_invoice_date)
    #     for line in formula_lines:
    #         if line.state not in ['sale', 'done']:
    #             continue
    #         result[line.id] = 100.0 - qty_invoiced.get(line.id, 0.0)
    #     return result
