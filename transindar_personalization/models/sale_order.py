##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, api, _
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    sale_preparetion_time = fields.Integer(
        compute='_compute_get_preparation_time',
        string='Tiempo De Preparacion',
    )

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        """Quieren que cuando se haga una devolucion, si se factura en dolares,
        se use la cotizacion de la confirmación de la venta (para no acreditar)
        mayor importe en pesos del que pago.
        Es un metodo medio engorroso ya que se pueden crear facturas desde
        varias ventas pero luego se devuelve un listado de facturas en total y
        nosotros queremos saber para las que son completamente devoluciones,
        la cotización a la fecha de la orden y del listado de factura no
        sabriamos cual es la orden de venta, por eso empezamos recorriendo
        las ordenes de venta.
        NOTA: si se quiere generalizar esto tener en cuenta que tal vez desde
        una OV en una moneda se podría estar facturando en esa moneda en otra
        cia que tenga esa moneda como base y habria algun tipo de inconsistencia
        """
        invoice_ids = []

        if final:
            other_currency_sales = self.filtered(
                lambda x: x.currency_id != x.company_id.currency_id)
            self -= other_currency_sales

            for other_currency_sale in other_currency_sales:
                invoice_ids += super(
                    SaleOrder, other_currency_sale).action_invoice_create(
                    grouped=grouped, final=final)
                for refund in self.env['account.invoice'].browse(
                    invoice_ids).filtered(
                    lambda x:
                        x.type == 'out_refund' and
                        x.currency_id != x.company_id.currency_id):

                    company_currency = refund.company_id.currency_id
                    original_invoices = self.env['account.invoice.line'].search(
                        [('sale_line_ids', 'in', refund.invoice_line_ids.
                          mapped('sale_line_ids').ids),
                         ('invoice_id.type', '=', 'out_invoice')]).mapped('invoice_id')
                    if not original_invoices:
                        continue
                    self.env['account.change.currency'].with_context(
                        active_id=refund.id).create({
                            'currency_to_id': company_currency.id,
                            'currency_rate': original_invoices.sorted(
                                lambda x: x.currency_rate)[0].currency_rate,
                            'change_type': 'value',
                            'save_secondary_currency': True,
                        }).change_currency()

        # self podria no tener elementos a estas alturas
        if self:
            invoice_ids += super(SaleOrder, self).action_invoice_create(
                grouped=grouped, final=final)
        return invoice_ids

    @api.multi
    def action_confirm(self):
        param = self.env['ir.config_parameter'].sudo().get_param(
            'sale_order_action_confirm')
        if param == 'tracking_disable':
            _logger.info('tracking_disable on SO confirm ')
            self = self.with_context(tracking_disable=True)
        elif param == 'mail_notrack':
            _logger.info('mail_notrack on SO confirm ')
            self = self.with_context(mail_notrack=True)
        res = super(SaleOrder, self).action_confirm()
        if param:
            self.message_post(
                body=_('Orden validada con "no tracking=%s"') % param)
        return res

    @api.multi
    def _compute_get_preparation_time(self):
        for rec in self.filtered(lambda x:
                                 x.company_id.preparation_time_variable):
            preparation_time_variable = (
                rec.company_id.preparation_time_variable)
            preparation_time_fixed = rec.company_id.preparation_time_fixed
            rec.sale_preparetion_time = len(
                rec.order_line) * preparation_time_variable + (
                preparation_time_fixed)

    @api.multi
    def update_requested_date(self):
        self.ensure_one()
        if self.sale_preparetion_time:
            self.requested_date = fields.Date.today() + timedelta(
                minutes=self.sale_preparetion_time)
