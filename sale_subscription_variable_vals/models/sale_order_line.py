##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    quantity_formula_id = fields.Many2one(
        'sale.order.line.vals_formula', string='Qty Formula', help='If you set a quantity formula, then when '
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
