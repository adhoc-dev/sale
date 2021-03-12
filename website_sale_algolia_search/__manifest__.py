# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Algolia Search on e-commerce',
    'version': '13.0.1.0.0',
    'category': 'Uncategorized',
    'author': 'ADHOC SA',
    'license': 'AGPL-3',
    'data': [
        'views/shop_templates.xml',
    ],
    'external_dependencies': {
        'python': ['algoliasearch']
    },
    'depends': [
        'base_algolia_search',
        'website_sale',
    ],
    'installable': True,
}
