##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    supplier_code = fields.Char(
        related='product_id.product_tmpl_id.supplier_code',
        readonly=True,
    )

    internal_code = fields.Char(
        related='product_id.internal_code',
        readonly=True,
    )

    product_brand_id = fields.Many2one(
        related='product_id.product_tmpl_id.product_brand_id',
        readonly=True,
    )

    additional_description = fields.Char()

    @api.onchange('additional_description')
    def change_additional_description(self):
        line = self.new({'product_id': self.product_id.id})
        line.product_id_change()
        name = line.name
        if self.additional_description:
            name = "%s\n%s" % (name, self.additional_description or '')
        self.name = name
