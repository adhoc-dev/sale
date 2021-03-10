{
    'name': "Account Balance",
    'version': '13.0.1.1.0',
    'category': 'Planner',
    'sequence': 14,
    'author': 'ADHOC SA',
    'website': 'www.adhoc.com.ar',
    'license': 'AGPL-3',
    'summary': 'Provides a wizard for importing initial account balances',
    "depends": [
        "l10n_ar_edi",
        "account_ux",
        "account_check",
    ],
    'data': [
        'views/account_onboarding_templates.xml',
        'wizards/account_balance_import_wizard.xml',
    ]
}