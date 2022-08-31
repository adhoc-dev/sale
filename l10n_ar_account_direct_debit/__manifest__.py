{
    'name': 'Direct Debits for Argentina',
    'version': "15.0.1.0.0",
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
        'demo/account_journal_demo.xml',
        'views/account_direct_debit_mandate_views.xml',
        'views/account_batch_payment_view.xml',
        'views/account_journal_views.xml',
    ],
    'demo': [
        'demo/account_direct_debit_mandate_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}