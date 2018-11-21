# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from odoo import models, api, fields


class ProductProduct(models.Model):

    _inherit = 'product.product'

    supplier_code = fields.Char(
        related='seller_ids.product_code',
        string="Supplier Code",
    )

    location_1 = fields.Char(
        related='product_tmpl_id.location_1',
        String='Location 1',
    )

    location_2 = fields.Char(
        related='product_tmpl_id.location_2',
        String='Location 2',
    )

    @api.multi
    def get_invoice_analisis(self):
        context = {
            'search_default_product_id': self.id,
            'search_default_partner_id': self._context.get(
                'partner_id', False)
        }

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.invoice.line.report',
            'view_mode': 'tree,graph',
            'view_type': 'form',
            'context': context,
        }
