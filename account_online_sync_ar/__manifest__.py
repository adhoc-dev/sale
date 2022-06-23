{
    'name': "Account Online Sync Argentina",
    'version': '15.0.1.0.0',
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
        'views/account_online_provider_views.xml',
        'views/account_journal_views.xml',

        "security/ir.model.access.csv",
        # TODO KZ revisar, creo que ya no seria necesario
        # access_account_online_link_id_manage,access_account_account_online_link_id manage,model_account_online_provider,account.group_account_manager,1,1,1,0
        # access_account_online_account_id_manage,access_account_online_account_id manage,model_account_online_journal,account.group_account_manager,1,1,1,0

        "data/ir_cron_data.xml",
        "wizards/provider_link_view.xml",
    ],
    'auto_install': True,
    'installable': True,
}
