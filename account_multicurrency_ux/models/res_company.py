from odoo import models, api, fields, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class ResCompany(models.Model):

    _inherit = "res.company"

    exchange_diff_adjustment_tolerance = fields.Float(
        # 'Tolerance for Exchange Diff. Adjustment',
        'Tolerancia para Ajuste por dif. de Cambio',
        digits=dp.get_precision('Discount'),
        help='Cuando una se imputa un pago a una factura de cliente con moneda secundaria, se marcará para realizar NC/ND de ajuste si'
        'si la diferencia de cotización entre la factura y el pago es mayor a este procentaje'
    )
    exchange_rate_tolerance = fields.Float(
        # 'Exchange rate Tolerance',
        'Tolerancia para tasa de cambio',
        digits=dp.get_precision('Discount'),
        help='En las facturas de ajuste por diferencia de cambio, permitir '
        'hasta este porcentaje de diferencia en la tasa de cambio respecto a '
        'tasa de cambio almacenada en odoo'
    )

    @api.constrains(
        'exchange_diff_adjustment_tolerance', 'exchange_rate_tolerance')
    def _check_exchange_fields(self):
        for rec in self:
            if rec.exchange_diff_adjustment_tolerance < 0.0:
                raise UserError(_(
                    'La Tolerancia para Ajuste por dif. de Cambio debe ser '
                    'mayor a cero.'))
            if rec.exchange_rate_tolerance < 0.0:
                raise UserError(_(
                    'La Diferencia permitida en tasa de cambio debe ser mayor '
                    'a cero.'))
