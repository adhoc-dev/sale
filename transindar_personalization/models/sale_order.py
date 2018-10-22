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
