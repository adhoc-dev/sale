{
    'name': 'Direct Debits Management',
    'version': "13.0.1.1.0",
    'category': 'Accounting/Accounting',
    'sequence': 14,
    'summary': '',
    'author': 'ADHOC SA',
    'website': 'www.adhoc.com.ar',
    'license': 'LGPL-3',
    'images': [
    ],
    'depends': [
        'account_batch_payment',
    ],
    'data': [
        'views/account_move_view.xml',
        'views/account_direct_debit_mandate_views.xml',
        'views/account_payment_views.xml',
        'views/account_journal_views.xml',
        'views/account_batch_payment_view.xml',
        'views/res_partner_view.xml',
        'data/account_payment_method_data.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
