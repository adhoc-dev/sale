##############################################################################
#
#    Copyright (C) 2019  ADHOC SA  (http://www.adhoc.com.ar)
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Accounting Multicurrency UX',
    'version': '13.0.1.0.0',
    'category': 'Accounting',
    'summary': '',
    'author': 'ADHOC SA',
    'website': 'www.adhoc.com.ar',
    'license': 'AGPL-3',
    'images': [
    ],
    'depends': [
        'account_ux',
        'account_payment_group',
    ],
    'data': [
        'wizards/account_exchange_diff_invoice_views.xml',
        'wizards/res_config_settings_views.xml',
        'views/account_move_views.xml',
        'views/account_partial_reconcile_views.xml',
        'views/account_payment_group_views.xml',
    ],
    'demo': [
    ],
    'installable': False,
    'auto_install': False,
    'application': False,
    'pre_init_hook': 'pre_init_hook',
}
