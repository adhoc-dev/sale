from odoo import models


class AccountJournal(models.Model):

    _inherit = 'account.journal'

    def action_choose_institution(self):
        """ Remove the normal account_online_sync and use the one in paybook """
        return self.env['account.online.provider'].with_context(journal_id=self.id)._paybook_open_login()

    def action_configure_bank_journal(self):
        """ Remove the normal account_online_sync and use the one in paybook """
        return self.env['account.online.provider'].with_context(journal_id=self.id)._paybook_open_login()

    def _compute_next_synchronization(self):
        """ Show paybook next sync date instead of next run date of ir.cron """
        super()._compute_next_synchronization()
        for rec in self.filtered(lambda x: x.account_online_provider_id.provider_type == 'paybook'):
            rec.next_synchronization = rec.account_online_provider_id.paybook_next_refresh
