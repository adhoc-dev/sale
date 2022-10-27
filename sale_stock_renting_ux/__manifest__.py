# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Sale Stock Renting UX',
    'category': 'Sales',
    'version': '13.0.1.2.0',
    'sequence': 14,
    'author': 'ADHOC SA',
    'website': 'www.adhoc.com.ar',
    'license': 'AGPL-3',
    'summary': 'Makes the rentings to do pickings when a product is rented',
    'depends': ['sale_stock_renting'],
    'data': [
                'views/res_config_settings.xml',
                'views/stock_picking_views.xml',
    ],
    'installable': False,
    'application': False
}
