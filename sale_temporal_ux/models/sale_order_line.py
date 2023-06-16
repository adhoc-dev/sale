from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _get_price_computing_kwargs(self):
        """ Override to add the pricing duration or the start and end date of temporal line """
        price_computing_kwargs = super()._get_price_computing_kwargs()
        price_computing_kwargs['order_state'] = self.order_id.state
        return price_computing_kwargs

    def _compute_pricelist_item_id(self):
        # assign temporal_type as False if temporal_type is set and use_time_based_rules is False
        # to avoid ignore the line when pricelist_item_id is computed (see sale_temporal inheritance).
        # This addition allows subscription products to segregate price and discount when the discount policy is "without_discount".
        # Without it, all base prices would include discounts (despite having other policy)
        # because pricelist_item_id would be set as False in _compute_pricelist_item_id.

        none_temporal_price = self.filtered(lambda x: x.temporal_type and not x.order_id.pricelist_id.use_time_based_rules)
        temporal_types = {x: x.temporal_type for x in none_temporal_price}
        none_temporal_price.temporal_type = False
        super(SaleOrderLine, self)._compute_pricelist_item_id()
        for k, v in temporal_types.items():
            k.temporal_type = v

    def  _compute_discount(self):
        """
        Cambiamos temporal_type para las suscripciones que no tienen time_based_rules para se comporten como una SO normal
        y tome el descuento aplicado.
        Ignoramos casos de upsell para que se calcule como lo hace nativamente odoo
        """
        # temporal lines con la opcion de time base rules desactivada y que no son uspell
        none_temporal_lines = self.filtered(
            lambda x: x.temporal_type and not x.order_id.pricelist_id.use_time_based_rules and x.order_id.subscription_management != 'upsell')
        temporal_types = {x: x.temporal_type for x in none_temporal_lines}
        # antes de ir a suepr borramos dato de temporal_type para que compute normal
        none_temporal_lines.temporal_type = False
        super()._compute_discount()
        # restauramos temporal_type orinal
        for k, v in temporal_types.items():
            k.temporal_type = v
