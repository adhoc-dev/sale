{
    'name': 'Website Sale Ribbon',
    'version': '13.0.1.0.0',
    'category': 'ecommerce',
    'author': 'ADHOC SA, 3Lines',
    'website': 'https://bitbucket.org/ingadhoc/adhoc-saas',
    'depends': [
        'website_sale'
    ],
    'data': [
        'views/product_ribbon_view.xml',
        'views/product_template_view.xml',
        'views/templates.xml',
        'security/ir.model.access.csv',
        'data/product_ribbon_data.xml',
    ],
    'uninstall_hook': 'uninstall_hook',
    'post_init_hook': 'post_init_hook',
    'installable': False,
    'auto_install': False,
    'application': False,
}
