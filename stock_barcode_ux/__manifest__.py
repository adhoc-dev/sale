
##############################################################################
#
#    Copyright (C) 2016  ADHOC SA  (http://www.adhoc.com.ar)
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
    'name': 'Stock Barcode UX',
    'category': 'Stock',
    'summary': 'Barcode Application',
    'version': '13.0.1.0.0',
    'author': 'ADHOC SA',
    'website': 'www.adhoc.com.ar',
    'license': 'AGPL-3',
    'depends': [
        'stock_barcode',
        'stock_ux',
    ],

    'data': [
        'views/abstract_client_action_extension_view.xml',
    ],
    'demo': [
    ],
    'application': False,
    'installable': False,
    'auto_install': False,
}
