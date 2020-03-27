from odoo import fields, models


class ProductRibbon(models.Model):

    _name = 'product.ribbon'
    _description = 'Product Ribbon'

    name = fields.Char(
        size=20,
        required=True,
        translate=True,
    )
    ribbon_color_back = fields.Char(
        'Background Color',
        required=True,
    )
    ribbon_color_text = fields.Char(
        'Font Color',
        required=True,
    )
