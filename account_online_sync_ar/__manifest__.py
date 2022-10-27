{
    'name': "Account Online Sync Argentina",
    'version': '15.0.1.5.0',
    'category': 'Accounting/Accounting',
    'sequence': 14,
    'author': 'ADHOC SA',
    'website': 'www.adhoc.com.ar',
    'license': 'AGPL-3',
    'summary': 'This module is used for Online bank synchronization for Argentina',
    "depends": [
        "account_online_synchronization",
    ],
    'data': [
        "views/templates.xml",
        "views/res_company_views.xml",
        'views/account_online_link_views.xml',
        'views/account_journal_views.xml',

        "security/ir.model.access.csv",
        "data/ir_cron_data.xml",
        "wizards/provider_link_view.xml",
        "wizards/account_link_journal_views.xml",
    ],
    'auto_install': True,
    'installable': False,
}
