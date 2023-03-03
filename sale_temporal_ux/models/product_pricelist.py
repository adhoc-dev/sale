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
        """ Modificamos este metodo para que si desactivamos el usar las reglas temporales esto devuelva False y _compute_price_rule
        calcule con las reglas de precio normales. Dejamos una clave en el contexto para poder evaluar en metodo _compute_price_rule si
        efectivamente estamos o no en esta situacion."""
        if not self.use_time_based_rules and not self._context.get('use_time_based_rules'):
            return False
        return super()._enable_temporal_price(start_date=start_date, end_date=end_date, duration=duration, unit=unit)

    def _compute_price_rule(
        self, products, qty, uom=None, date=False, start_date=None, end_date=None, duration=None,
        unit=None, **kwargs
    ):
        self.ensure_one()

        if not products:
            return {}

        results = {}

        # si la tarifa tiene desactivao lo de usar reglas temporales y venimos de una orden de venta confirmada, y estamos pidiendo un precio temporal (suscripcion)
        # entonces, actualizamos la fecha a ahora porque si no, con el cambio que hacemos en _enable_temporal_price, para este caso se va a calcular
        # con las reglas de tarifa pero usando la fecha de la orden (que puede ser super vieja) y para cotizaciones y demas queremos la fecha actual
        # es importante el chequeo del estado de la orden porque en la misma si la suscripcion esta en borrador si queremos que al actualizar precios se calcule teniendo
        # en cuenta fecha de la orden
        if not self.use_time_based_rules and kwargs.get('order_state', False) in ('sale', 'done') and self.with_context(
                use_time_based_rules=True)._enable_temporal_price(start_date, end_date, duration, unit):
            date = fields.Datetime.now()
        return super()._compute_price_rule(
            products, qty, uom=uom, date=date, start_date=start_date, end_date=end_date, duration=duration, unit=unit, **kwargs)
