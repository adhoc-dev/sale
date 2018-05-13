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
    'name': 'Transindar Personalization',
    'category': 'Stock',
    'version': '9.0.2.6.0',
    'description': """
Transindar Personalization
==========================
    """,
    'author': 'ADHOC SA',
    'website': 'www.adhoc.com.ar',
    'license': 'AGPL-3',
    'depends': [
        # dependencias no necesarias
        # 'base_name_search_improved',
        # 'product_category_full_name_search',
        # 'l10n_ar_account',
        # 'l10n_ar_afipws_fe',
        # 'account_accountant',
        # 'account_debt_management',
        # 'account_move_helper',
        # 'account_no_translation',
        # 'base_currency_inverse_rate',
        # 'account_clean_cancelled_invoice_number',
        # 'account_invoice_change_currency',
        # 'account_invoice_commercial',
        # 'account_invoice_company_search',
        # 'account_invoice_journal_group',
        # 'account_invoice_prices_update',
        # 'account_invoice_tax_wizard',
        # 'l10n_ar_aeroo_einvoice',
        # 'l10n_ar_aeroo_purchase',
        # 'l10n_ar_aeroo_sale',
        # 'l10n_ar_aeroo_stock',
        # 'l10n_ar_aeroo_payment_group',
        # 'l10n_ar_padron_afip',
        # 'l10n_ar_bank',
        # 'product_catalog_aeroo_report_public_categ',
        # 'product_no_translation',
        # 'product_price_currency',
        # 'product_pricelist',
        # 'product_template_search_by_barcode',
        # 'purchase_quotation_products',
        # 'sale_exception_credit_limit',
        # 'sale_exception_partner_state',
        # 'sale_quotation_products',
        # 'stock_inventory_preparation_filter',
        # 'base_state_active',
        # 'base_technical_features',

        # dependencias para vistas
        'product_supplier_search',
        'stock_picking_control',
        'account_payment_group',
        'product_replenishment_cost_rule',
        'product_price_taxes_included',
        'product_sale_price_by_margin',
        'sale_global_three_discounts',
        'sale_exception_price_security',
        'sale_stock_availability',
        'product_brand',
        'product_website_categ_search',
        'sale_order_validity',
        'sale_quotation_products',
        'sale_three_discounts',
        'sale_global_discount',
        # 'partner_internal_code',
        'product_internal_code',
        # 'partner_no_auto_search',
        # 'product_no_auto_search',
        # no migrados todavia
        # 'stock_picking_list',
        # 'account_invoice_prices_update',
        # 'product_template_tree_prices',
        'account_invoice_control',
        'sale_order_type',
        'sale_order_dates',
        'purchase_usability',
        'product_replenishment_cost',
        # no se migran
        # dependencias para que el no_tracking vaya lo mas arriba posible
        'sale_order_type_automation',
        'sale_order_type_invoice_policy',
        'sale_procurement_date_confirm',
        'sale_order_validity',
    ],
    'data': [
        # 'security/security.xml',
        # 'sale_order_view.xml',
        # 'product_view.xml',
        # 'account_payment_view.xml',
        # 'category_public_view.xml',
        # 'category_public_view.xml',
        # 'invoice_view.xml',
        # already noupdate on production
        # 'res_partner_view.xml',
        # 'stock_picking_view.xml',
        # 'res_company_view.xml'
    ],
    'demo': [
        # 'demo/load_es_lang.yml',
    ],
    'test': [],
    'installable': False,
    'auto_install': False,
    'application': False,
}
