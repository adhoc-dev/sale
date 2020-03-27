# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Margins in Subscriptions',
    'category': 'Sales',
    'version': '13.0.1.0.0',
    'sequence': 14,
    'author': 'ADHOC SA',
    'website': 'www.adhoc.com.ar',
    'license': 'AGPL-3',
    'summary': 'Calculate margins and profitabilities in subscriptions',
    'depends': ['sale_subscription'],
    'data': ['views/sale_subscription_margin_view.xml'],
    'installable': True,
    'application': False
}
