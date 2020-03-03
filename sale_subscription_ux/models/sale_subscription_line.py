##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api


class SaleSubscriptionLine(models.Model):
    """
    We use the analogous methods to the sale.order.line for the
     calculation of the unit price with discount.
    """

    _inherit = "sale.subscription.line"

    sequence = fields.Integer(
        'Sequence',
        required=True,
        default=10,
        help="The sequence field is used to order lines"
    )

    def _get_display_price(self, product, pricelist):
        product_context = dict(
            self.env.context,
            partner_id=self.analytic_account_id.partner_id.id,
            date=fields.Date.today(), uom=self.uom_id.id)
        final_price, rule_id = pricelist.with_context(
            product_context).get_product_price_rule(
            self.product_id, self.quantity or 1.0,
            self.analytic_account_id.partner_id)
        base_price, currency_id = self.with_context(
            product_context)._get_real_price_currency(
            product, rule_id, self.quantity, self.uom_id, pricelist.id)
        if currency_id != pricelist.currency_id.id:
            base_price = self.env['res.currency'].browse(
                currency_id).with_context(
                product_context).compute(
                    base_price, pricelist.currency_id)
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

    @api.onchange('product_id', 'quantity')
    def onchange_product_quantity(self):
        res = super(SaleSubscriptionLine, self).onchange_product_quantity()
        if hasattr(self, '_origin') and self._origin \
                and self.analytic_account_id.template_id.do_not_update_price \
                and self._origin.read(
                    ["quantity"])[0]["quantity"] != self.quantity \
                and self._origin.read(["product_id"])[0]["product_id"][0] == \
                self.product_id.id:
            self.price_unit = self._origin.price_unit
            return res
        pricelist = self.analytic_account_id.pricelist_id
        if self.product_id and \
                pricelist.discount_policy == 'without_discount':
            product = self.product_id.with_context(
                lang=self.analytic_account_id.partner_id.lang,
                partner=self.analytic_account_id.partner_id.id,
                quantity=self.quantity,
                date=fields.Date.today(),
                pricelist=pricelist.id,
                uom=self.uom_id.id
            )
            self.price_unit = self._get_display_price(product, pricelist)
        return res

    @api.onchange('product_id', 'price_unit', 'uom_id', 'quantity')
    def _onchange_discount(self):
        if not (self.product_id and self.uom_id and
                self.analytic_account_id.partner_id and
                self.analytic_account_id.pricelist_id and
                self.analytic_account_id.pricelist_id.
                discount_policy == 'without_discount' and
                self.env.user.has_group('product.group_discount_per_so_line')):
            return

        self.discount = 0.0
        pricelist = self.analytic_account_id.pricelist_id
        product = self.product_id.with_context(
            lang=self.analytic_account_id.partner_id.lang,
            partner=self.analytic_account_id.partner_id.id,
            quantity=self.quantity,
            date=fields.Date.today(),
            pricelist=pricelist.id,
            uom=self.uom_id.id,
            fiscal_position=self.env.context.get('fiscal_position')
        )
        product_context = dict(
            self.env.context,
            partner_id=self.analytic_account_id.partner_id.id,
            date=fields.Date.today(), uom=self.uom_id.id)
        price, rule_id = pricelist.with_context(
            product_context).get_product_price_rule(
            self.product_id, self.quantity or 1.0, self.
            analytic_account_id.partner_id)
        new_list_price, currency_id = self.with_context(
            product_context)._get_real_price_currency(
            product, rule_id,
            self.quantity, self.uom_id,
            pricelist.id)

        if new_list_price != 0:
            if self.analytic_account_id.\
                    pricelist_id.currency_id.id != currency_id:
                # we need new_list_price in the same currency as price,
                # which is in the Subscription's pricelist's currency
                new_list_price = self.env['res.currency'].browse(
                    currency_id).with_context(
                    product_context).compute(
                        new_list_price,
                        pricelist.currency_id)
            discount = (new_list_price - price) / new_list_price * 100
            if discount > 0:
                self.discount = discount

    def _get_real_price_currency(
            self, product, rule_id, qty, uom, pricelist_id):
        """Retrieve the price before applying the pricelist
            :param obj product: object of current product record
            :parem float qty: total quentity of product
            :param tuple price_and_rule: tuple(price, suitable_rule)
            coming from pricelist computation
            :param obj uom: unit of measure of current order line
            :param integer pricelist_id: pricelist id of sales order"""
        PricelistItem = self.env['product.pricelist.item']
        field_name = 'lst_price'
        currency_id = None
        product_currency = None
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            if pricelist_item.pricelist_id.\
                    discount_policy == 'without_discount':
                while pricelist_item.base == 'pricelist' and \
                    pricelist_item.base_pricelist_id and\
                        pricelist_item.base_pricelist_id.discount_policy\
                        == 'without_discount':
                    price, rule_id = pricelist_item.\
                        base_pricelist_id.with_context(
                            uom=uom.id).get_product_price_rule(
                            product, qty, self.analytic_account_id.partner_id)
                    pricelist_item = PricelistItem.browse(rule_id)

            if pricelist_item.base == 'standard_price':
                field_name = 'standard_price'
            if pricelist_item.base == 'pricelist' and\
                    pricelist_item.base_pricelist_id:
                field_name = 'price'
                product = product.with_context(
                    pricelist=pricelist_item.base_pricelist_id.id)
                product_currency = pricelist_item.base_pricelist_id.currency_id
            currency_id = pricelist_item.pricelist_id.currency_id

        product_currency = product_currency or(
            product.company_id and product.company_id.currency_id
        ) or self.env.company.currency_id
        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(
                    product_currency, currency_id,
                    self.analytic_account_id.company_id or self.env.company, fields.Date.today())

        product_uom = self.env.context.get('uom') or product.uom_id.id
        if uom and uom.id != product_uom:
            # the unit price is in a different uom
            uom_factor = uom._compute_price(1.0, product.uom_id)
        else:
            uom_factor = 1.0

        return product[field_name] * uom_factor * cur_factor, currency_id.id
