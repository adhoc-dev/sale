from odoo import api, fields, models


class ProductTemplate(models.Model):

    _inherit = "product.template"

    ribbon_id = fields.Many2one(
        'product.ribbon',
    )

    @api.onchange('ribbon_id')
    def _onchange_ribbon_id(self):
        style = self.env.ref('website_sale.image_promo')
        if self.ribbon_id:
            self.write({'website_style_ids': [(4, style.id)]})
        else:
            self.write({'website_style_ids': [(3, style.id)]})
