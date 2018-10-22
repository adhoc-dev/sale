# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, api
import logging

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def action_date_assign(self):
        param = self.env['ir.config_parameter'].sudo().get_param(
                'account_invoice_action_date_assign')
        if param == 'tracking_disable':
            _logger.info('tracking_disable on invoice date_assign ')
            self = self.with_context(tracking_disable=True)
        elif param == 'mail_notrack':
            _logger.info('mail_notrack on invoice date_assign ')
            self = self.with_context(mail_notrack=True)
        return super(AccountInvoice, self).action_date_assign()

    @api.multi
    def action_move_create(self):
        param = self.env['ir.config_parameter'].sudo().get_param(
                'account_invoice_action_move_create')
        if param == 'tracking_disable':
            _logger.info('tracking_disable on invoice move_create ')
            self = self.with_context(tracking_disable=True)
        elif param == 'mail_notrack':
            _logger.info('mail_notrack on invoice move_create ')
            self = self.with_context(mail_notrack=True)
        return super(AccountInvoice, self).action_move_create()

    @api.multi
    def invoice_validate(self):
        param = self.env['ir.config_parameter'].sudo().get_param(
                'account_invoice_invoice_validate')
        if param == 'tracking_disable':
            _logger.info('tracking_disable on invoice invoice_validate ')
            self = self.with_context(tracking_disable=True)
        elif param == 'mail_notrack':
            _logger.info('mail_notrack on invoice invoice_validate ')
            self = self.with_context(mail_notrack=True)
        return super(AccountInvoice, self).invoice_validate()
