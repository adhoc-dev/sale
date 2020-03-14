##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class PurchaseSubscriptionLine(models.Model):
    _name = "purchase.subscription.line"
    _description = "Purchase Subscription Line"

    purchase_subscription_id = fields.Many2one(
        'purchase.subscription',
        'Subscription',
        index=True,
        ondelete='cascade',
    )
    quantity = fields.Float(
        'Quantity',
        compute='_compute_quantity',
    )
    purchase_quantity = fields.Float(
        default=1.0,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
    )
    name = fields.Text(
        'Description',
        required=True,
    )
    uom_id = fields.Many2one(
        'uom.uom',
        'Unit of Measure',
        required=True,
    )
    price_unit = fields.Float(
        'Unit Price',
        required=True,
    )
    discount = fields.Float(
        'Discount (%)',
        digits='Discount',
    )
    price_subtotal = fields.Float(
        compute='_compute_amount_line',
        string='Sub Total',
        digits='Account',
    )

    @api.depends(
        'product_id',
        'quantity',
        'discount',
        'purchase_subscription_id.currency_id'
    )
    def _compute_amount_line(self):
        AccountTax = self.env['account.tax']
        for line in self:
            price = line.product_id.taxes_id._fix_tax_included_price(
                line.price_unit, line.product_id.sudo().taxes_id, AccountTax)
            price_subtotal = line.quantity * price * (100.0 - line.discount) / 100.0
            price_subtotal = line.purchase_subscription_id.sudo().currency_id.round(price_subtotal) if \
                line.purchase_subscription_id.sudo().currency_id else price_subtotal
            line.price_subtotal = price_subtotal

    @api.depends('purchase_quantity')
    def _compute_quantity(self):
        for rec in self:
            rec.quantity = rec.purchase_quantity

    @api.onchange('product_id')
    def product_id_change(self):
        product = self.product_id.with_context({
            'lang': self.purchase_subscription_id.partner_id.lang,
            'partner_id': self.purchase_subscription_id.partner_id.id,
        })
        name = product.display_name
        if product.name:
            name = product.name_get()[0][1]
            if product.description_purchase:
                name += '\n' + product.description_purchase

        uom = self.uom_id or product.uom_id or False
        price_unit = product.standard_price
        if product:
            seller = product._select_seller(
                partner_id=self.purchase_subscription_id.partner_id,
                quantity=self.quantity,
                uom_id=uom)
            if seller:
                price_unit = seller.price
                if price_unit and seller and self.\
                    purchase_subscription_id.\
                    currency_id and seller.currency_id != self.\
                        purchase_subscription_id.currency_id:
                    price_unit = seller.currency_id.compute(
                        price_unit,
                        self.purchase_subscription_id.currency_id)

                if seller and uom and seller.\
                        product_uom != uom:
                    price_unit = seller.product_uom._compute_price(
                        price_unit, uom)

            if uom != product.uom_id:
                price_unit = product.uom_id._compute_price(
                    price_unit, uom)

        self.update({
            'name': name,
            'uom_id': uom,
            'price_unit': price_unit,
        })
        if uom:
            return {'domain': {'uom_id': [
                ('category_id', '=', product.uom_id.category_id.id)]}}
        else:
            return {'domain': {'uom_id': []}}

    @api.onchange('uom_id')
    def product_uom_change(self):
        if not self.uom_id:
            self.update({
                'price_unit': 0.0,
                'uom_id': self.uom_id or False,
            })
        self.product_id_change()
