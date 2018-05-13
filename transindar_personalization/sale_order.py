##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, api, _
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    sale_preparetion_time = fields.Integer(
        compute='_get_preparation_time',
        string='Tiempo De Preparacion')

    @api.multi
    def action_confirm(self):
        param = self.env['ir.config_parameter'].get_param(
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

    @api.one
    def _get_preparation_time(self):
        if self.company_id.preparation_time_variable:
            preparation_time_variable = (
                self.company_id.preparation_time_variable)
            preparation_time_fixed = self.company_id.preparation_time_fixed
            self.sale_preparetion_time = len(
                self.order_line) * preparation_time_variable + (
                preparation_time_fixed)

    @api.one
    def update_requested_date(self):
        if self.sale_preparetion_time:
            self.requested_date = datetime.today() + timedelta(
                minutes=self.sale_preparetion_time)


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    supplier_code = fields.Char(
        related='product_id.product_tmpl_id.supplier_code',
        readonly=True)
    internal_code = fields.Char(
        related='product_id.internal_code',
        readonly=True)
    product_brand_id = fields.Many2one(
        related='product_id.product_tmpl_id.product_brand_id',
        readonly=True)
    additional_description = fields.Char(
    )

    @api.one
    @api.onchange('additional_description')
    def change_additional_description(self):
        line = self.new({'product_id': self.product_id.id})
        line.product_id_change()
        name = line.name
        if self.additional_description:
            name = "%s\n%s" % (name, self.additional_description or '')
        self.name = name
