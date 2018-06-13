##############################################################################
#
#    Copyright (C) 2015  ADHOC SA  (http://www.adhoc.com.ar)
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
    "name": "Purchase Subscription",
    'version': '11.0.1.0.0',
    'category': 'Accounting',
    'sequence': 14,
    'summary': 'Subscription, Invoicing',
    'author': 'ADHOC SA',
    'website': 'www.adhoc.com.ar',
    'license': 'AGPL-3',
    'images': [
    ],
    'depends': [
        'purchase',
    ],
    'data': [
        'security/purchase_subscription_security.xml',
        'security/ir.model.access.csv',
        'views/purchase_subscription_views.xml',
        'data/email_template_data.xml',
        'data/ir_cron_data.xml',
        'data/purchase_subscription_close_reason_data.xml',
        'data/ir_sequence_data.xml'
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
