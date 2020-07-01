{
    'name': "Account Online Sync Argentina",
    'version': '13.0.1.0.0',
    'category': 'Accounting/Accounting',
    'sequence': 14,
    'author': 'ADHOC SA',
    'website': 'www.adhoc.com.ar',
    'license': 'AGPL-3',
    'summary': 'This module is used for Online bank synchronization for Argentina',
    "depends": [
        "account_online_sync",
        "saas_client",
    ],
    'data': [
        "views/templates.xml",
        "views/res_company_views.xml",
        'views/account_online_provider_views.xml',
        "security/ir.model.access.csv",
    ]
}
