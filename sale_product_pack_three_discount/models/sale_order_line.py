##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, api


class SaleOrder(models.Model):
    _inherit = "sale.order.line"

    @api.depends("product_id", "product_uom", "product_uom_qty")
    def _compute_discount(self):
        res = super()._compute_discount()
        for pack_line in self.filtered("pack_parent_line_id"):
            pack_line.discount1 = pack_line._get_pack_line_discount()
        return res
