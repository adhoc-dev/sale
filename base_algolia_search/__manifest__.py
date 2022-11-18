# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Algolia Search',
    'summary': 'Algolia search on name_search and search views',
    'version': "15.0.1.0.0",
    'category': 'Uncategorized',
    'author': 'ADHOC SA',
    'license': 'AGPL-3',
    'data': [
        'views/ir_model_views.xml',
        'data/ir_cron_data.xml',
        'data/ir_parameter_data.xml',
        'security/ir.model.access.csv',
    ],
    'depends': [
        'base',
    ],
    'external_dependencies': {
        'python': [
            'algoliasearch'
        ],
    },
    'installable': False,
    "uninstall_hook": "uninstall_hook",
}
