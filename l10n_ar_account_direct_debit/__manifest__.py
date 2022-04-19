{
    'name': 'Direct Debits for Argentina',
    'version': "13.0.1.0.0",
    'category': 'Accounting/Accounting',
    'sequence': 14,
    'summary': '',
    'author': 'ADHOC SA',
    'website': 'www.adhoc.com.ar',
    'license': 'LGPL-3',
    'images': [
    ],
    'depends': [
        'account_direct_debit',
    ],
    'data': [
        'views/account_direct_debit_mandate_views.xml',
        'views/account_batch_payment_view.xml',
        'views/res_config_settings_views.xml',
        'wizards/account_batch_payment_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
