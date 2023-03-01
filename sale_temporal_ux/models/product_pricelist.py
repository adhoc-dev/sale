from odoo import fields, models


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    use_time_based_rules = fields.Boolean(
        default=True,
        help='Con esta opción activa puede definir "Reglas basada en tiempo". Estas reglas se utilizan para calcular '
        'distintos precios de venta según el período que se este utilizando (mes, año, etc) en apps como Alquileres o '
        'Sucripciones. Ahora bien, con esta opción activa, los calculos de precios basados en tiempo no se combinan '
        'con las reglas de precio que son mas flexibles y permiten, entre otras cosas, basar una tarifa en otra'
    )

    def _enable_temporal_price(self, start_date=None, end_date=None, duration=None, unit=None):
        if not self.use_time_based_rules:
            return False
        return super()._enable_temporal_price(start_date=start_date, end_date=end_date, duration=duration, unit=unit)
