from . import models
from odoo.api import Environment, SUPERUSER_ID


def uninstall_hook(cr, registry):
    env = Environment(cr, SUPERUSER_ID, {})
    style = env.ref('website_sale.image_promo')
    sale_ribbon = env.ref('website_sale_ribbon.sale_product_ribbon')
    products = env['product.template'].search([
        ('ribbon_id', '=', sale_ribbon.id)])
    products.write({
        'website_style_ids': [(4, style.id)],
    })
    style.write({'name': 'Sale Ribbon'})


def post_init_hook(cr, registry):
    env = Environment(cr, SUPERUSER_ID, {})
    style = env.ref('website_sale.image_promo')
    sale_ribbon = env.ref('website_sale_ribbon.sale_product_ribbon')
    # Set Sale ribbon by default to the products that have Sale Ribbon style
    products = env['product.template'].search([
        ('website_style_ids', 'in', style.id),
    ])
    products.write({
        'ribbon_id': sale_ribbon.id,
    })
    # Change Sale Ribbon Style name to Show Ribbon, This to avoid confusion.
    style.write({'name': 'Show Ribbon'})
