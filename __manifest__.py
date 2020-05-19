{
    'name': "Account Balance",
    'version': '12.0.1.0.0',
    'category': 'Planner',
    'sequence': 14,
    'author': 'ADHOC SA',
    'website': 'www.adhoc.com.ar',
    'license': 'AGPL-3',
    'summary': 'Provides a wizard for importing initial account balances',
    "depends": [
        "l10n_ar_afipws_fe",
        "account_ux",
        "account_check",
    ],
    'data': [
        'wizards/account_balance_import_wizard.xml',
    ]
}
