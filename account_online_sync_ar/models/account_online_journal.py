# -*- coding: utf-8 -*-
from odoo import models
from datetime import datetime


class PaybookAccount(models.Model):

    _inherit = 'account.online.journal'

    """ The paybook account that is saved in Odoo. It knows how to fetch Paybook to get the new bank statements """

    def retrieve_transactions(self):
        """ Get transsanctions from provider, prepare data, and create bank statements """
        if (self.account_online_provider_id.provider_type != 'paybook'):
            return super().retrieve_transactions()
        if not self.journal_ids:
            return 0

        self.ensure_one()
        last_sync = datetime.combine(self.last_sync, datetime.min.time())
        params = {'id_credential': self.account_online_provider_id.provider_account_identifier,
                  'id_account': self.online_identifier,
                  'dt_transaction_from': last_sync.strftime('%s')}

        response = self.account_online_provider_id._paybook_fetch('GET', '/transactions', params, {})
        transactions = []
        for trx in response:
            if trx.get('is_pending') != 0 or trx.get('is_disable') != 0 or trx.get('is_deleted') != 0:
                continue
            date = trx.get('dt_transaction')  # dt_transaction dt_refresh dt_disable dt_deleted
            trx_data = {
                'date': datetime.fromtimestamp(date).date(),
                'online_identifier': trx.get('id_transaction'),
                'name': trx.get('description'),
                'amount': trx.get('amount'),
                'end_amount': self.balance,
                'ref': trx.get('reference') or ''}
            extra_data = trx.get('extra')
            if extra_data:
                if "order" in extra_data:
                    trx_data['sequence'] = extra_data.get('order')
                if "caption" in extra_data:
                    trx_data['name'] += ' - ' + extra_data.get('caption')
                if "caption2" in extra_data:
                    trx_data['name'] += ' - ' + extra_data.get('caption2')
            transactions.append(trx_data)
        return self.env['account.bank.statement'].online_sync_bank_statement(transactions, self.journal_ids)
