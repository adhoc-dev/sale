from odoo import models, fields


class AccountJournal(models.Model):

    _inherit = 'account.journal'

    paybook_last_transaction = fields.Datetime(
        'Last synced transaction', related='account_online_provider_id.last_refresh', readonly=False)
    paybook_next_available = fields.Datetime(
        related='account_online_provider_id.paybook_next_refresh', readonly=False)

    account_online_provider_type = fields.Selection(
        related='account_online_journal_id.account_online_provider_id.provider_type', readonly=False)

    def action_choose_institution(self):
        """ Remove the normal account_online_sync and use the one in paybook """
        return self.env['account.online.provider'].with_context(journal_id=self.id)._paybook_open_login()

    def action_configure_bank_journal(self):
        """ Remove the normal account_online_sync and use the one in paybook """
        return self.env['account.online.provider'].with_context(journal_id=self.id)._paybook_open_login()
