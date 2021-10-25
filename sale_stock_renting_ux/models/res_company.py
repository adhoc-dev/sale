from odoo import fields, models

class ResCompany(models.Model):
    _inherit = "res.company"

    rental_picking_type_id = fields.Many2one('stock.picking.type', string='Rental Delivery Default Picking Type')

