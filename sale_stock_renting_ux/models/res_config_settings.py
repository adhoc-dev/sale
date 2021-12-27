from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    rental_create_picking = fields.Boolean(
        string='Create picking on rentals',
        config_parameter='sale_stock_renting_ux.rental_create_picking')
    rental_picking_type_id = fields.Many2one('stock.picking.type', related="company_id.rental_picking_type_id",
        string='Default Picking Type',readonly=False, domain="[('company_id', '=', company_id)]")
