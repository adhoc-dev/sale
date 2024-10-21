from odoo import api, models
import logging

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _get_tax_included_unit_price_from_price(
        self, product_price_unit, product_taxes,
        fiscal_position=None,
        product_taxes_after_fp=None,
    ):
        """Modificamos para que como se obtienen los precios no tenga en cuenta en nada la fiscal position.
        Sin este cambio, en una venta con posicion fiscal que reemplace IVA 21 a exento (o no gravado), si se recalcula
        el precio (cambiando cantidad o agregando producto) y el impuesto es con opcion "incluido", el precio que se
        usa es descontando el impuesto original en vez del precio final
        """
        return super()._get_tax_included_unit_price_from_price(
            product_price_unit, product_taxes, product_taxes_after_fp=product_taxes_after_fp,
            fiscal_position=False)
