from odoo import models, fields
from odoo.tools.safe_eval import safe_eval


class AccountBankStatementLine(models.Model):

    _inherit = 'account.bank.statement.line'

    def unlink(self):
        """ overwrite in order to save history information in the related account.online.journal."""
        data = {}
        online_txs = self.filtered(lambda x: x.online_transaction_identifier)
        for account_online_journal in online_txs.mapped('online_account_id'):
            data[account_online_journal] = [(tx.online_transaction_identifier, tx.date.strftime('%d/%m/%Y')) for tx in online_txs.filtered(
                lambda x: x.online_account_id == account_online_journal)]
        res = super().unlink()
        self.register_deleted_transactions(data)
        return res

    def register_deleted_transactions(self, data):
        """ receive the data of the deleted transactions grouped by account online journal.
        Write in the account.onlint.jounal the information about the deleted transaction (id, who did it, when) """
        for (account_online_journal, transactions) in data.items():
            dicc = safe_eval(account_online_journal.transactions_blacklist)
            for tx in transactions:
                id_transaction = tx[0]
                transaction_date = tx[1]
                user = self.env.user.id
                fecha_eliminacion = fields.Date.today().strftime('%d/%m/%Y')
                if transaction_date in dicc:
                    dicc[transaction_date] += [(id_transaction, user, fecha_eliminacion)]
                else:
                    dicc[transaction_date] = [(id_transaction, user, fecha_eliminacion)]
            account_online_journal.transactions_blacklist = dicc
