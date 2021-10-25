from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_rental_picking = fields.Boolean(related='sale_id.is_rental_order')
