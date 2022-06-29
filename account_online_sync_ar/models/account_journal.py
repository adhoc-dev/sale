from odoo import api, models, fields
from odoo.exceptions import UserError


class AccountJournal(models.Model):

    _inherit = 'account.journal'

    paybook_last_transaction = fields.Datetime(
        'Last synced transaction', related='account_online_link_id.last_refresh', readonly=False)
    account_online_provider_type = fields.Selection(
        related='account_online_link_id.provider_type', readonly=False)

    # TODO KZ Este ya no existe en el original ver con que debemos reemplazarlo
    # def action_choose_institution(self):
    #     """ Remove the normal account_online_sync and use the one in paybook """
    #     default_action = self.action_configure_bank_journal()
    #     provider_link = self.env['provider.link'].create({'journal_id': self.id, 'default_action': default_action})
    #     return provider_link.choose()

    # TODO No estamos haciendo nada asi que lo comento, capaz tengamos que borrarlo
    # def action_configure_bank_journal(self):
    #     """ Remove the normal account_online_sync and use the one in paybook """
    #     default_action = super().action_configure_bank_journal()
    #     return default_action

    @api.model
    def _cron_fetch_online_transactions(self):
        """ Only run cron for paybook provider synchronization record status is OK or if we receive any 5xx Connection
        Error Codes """
        online_acc_journal = self.search([('account_online_account_id', '!=', False)])
        saltedge_journals = online_acc_journal.filtered(lambda x: x.account_online_link_id.provider_type != 'paybook')

        if saltedge_journals:
            super(AccountJournal, saltedge_journals)._cron_fetch_online_transactions()

        paybook_journals = online_acc_journal - saltedge_journals
        for journal in paybook_journals:
            online_link = journal.account_online_link_id
            if online_link.auto_sync and (online_link.state == 'connected' or online_link.status_code in ['406', '500', '501', '503', '504', '509']):
                try:
                    online_link._fetch_transactions()
                    # for cron jobs it is usually recommended to commit after each iteration, so that a later error or job timeout
                    # doesn't discard previous work
                    self.env.cr.commit()
                except UserError:
                    pass

    def cron_paybook_update_transactions(self):
        """ method called from schedule action that will try to update/fix refreshed paybook transactions in odoo """
        journals = self.search([('account_online_account_id', '!=', False)])
        if not journals:
            return
        for paybook_link in journals.mapped('account_online_link_id').filtered(lambda x: x.provider_type == 'paybook'):
            try:
                paybook_link.action_paybook_update_transactions()
            except UserError:
                continue
