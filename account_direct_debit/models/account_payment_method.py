from odoo import models, api
import logging
_logger = logging.getLogger(__name__)


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res['dd'] = {'mode': 'multi', 'domain': [('type', '=', 'bank')]}
        return res