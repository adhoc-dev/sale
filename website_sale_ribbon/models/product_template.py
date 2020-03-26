from odoo import fields, models


class ProductTemplate(models.Model):

    _inherit = "product.template"

    ribbon_id = fields.Many2one(
        'product.ribbon',
    )
