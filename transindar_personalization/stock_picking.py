# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, api
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def do_new_transfer(self):
        param = self.env['ir.config_parameter'].get_param(
                'stock_picking_do_transfer')
        if param == 'tracking_disable':
            _logger.info('tracking_disable on Picking do_new_transfer ')
            self = self.with_context(tracking_disable=True)
        elif param == 'mail_notrack':
            _logger.info('mail_notrack on Picking do_new_transfer ')
            self = self.with_context(mail_notrack=True)
        return super(StockPicking, self).do_new_transfer()

    @api.multi
    def do_transfer(self):
        param = self.env['ir.config_parameter'].get_param(
                'stock_picking_do_transfer')
        if param == 'tracking_disable':
            _logger.info('tracking_disable on Picking confirm ')
            self = self.with_context(tracking_disable=True)
        elif param == 'mail_notrack':
            _logger.info('mail_notrack on Picking confirm ')
            self = self.with_context(mail_notrack=True)
        return super(StockPicking, self).do_transfer()
