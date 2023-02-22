{
    'name': "Account Balance",
    'version': "16.0.1.1.0",
    'category': 'Planner',
    'sequence': 14,
    'author': 'ADHOC SA',
    'website': 'www.adhoc.com.ar',
    'license': 'AGPL-3',
    'summary': 'Provides a wizard for importing initial account balances',
    "depends": [
        "account_ux",
        "l10n_latam_check",
        'account_payment_group',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_onboarding_templates.xml',
        'wizards/account_balance_import_wizard.xml',
    ],
    'installable': True,
}
