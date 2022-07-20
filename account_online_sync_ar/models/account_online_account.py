# -*- coding: utf-8 -*-
from odoo import _, api, models
from datetime import datetime


class PaybookAccount(models.Model):

    _inherit = 'account.online.account'

    """ The paybook account that is saved in Odoo. It knows how to fetch Paybook to get the new bank statements """

    @api.model
    def _update_with_value(self, trx_data, field_to_set, value):
        if value:
            old_value = trx_data.get(field_to_set)
            trx_data[field_to_set] = old_value + ' - ' + str(value) if old_value else str(value)

    def _retrieve_transactions(self):
        """ Get transsanctions from provider, prepare data, and create bank statements """
        if self.account_online_link_id.provider_type != 'paybook':
            return super()._retrieve_transactions()

        transactions = self.paybook_get_transactions()
        return self.env['account.bank.statement']._online_sync_bank_statement(transactions, self)

    def write(self, values):
        """ Hacemos track en el chatter del provider de cuando un usuario modifica la fecha de ultima sincronizacion
        de las cuentas bancarias asociadas. Esto seria necesario cuando lo hace el usuario de manera particular y no
        a traves del cron """
        # Estamos guardado el valor previo que tenia el campo last_refresh
        last_value = {}
        for rec in self:
            if 'last_sync' in values:
                last_value.update({rec.id: rec.last_sync})

        # Ejecutamos el write normal
        res = super().write(values)

        # Si tenemos cambios en last_refresh entonces colocamos mensaje en el chatter del
        # account.provider indicando el cambio
        # colocar que sea un usuario que no sea el que corre el ir.cron.
        if last_value and not self.env.user.has_group("saas_client.group_saas_support"):
            for rec in self:
                rec.account_online_link_id.message_post(body=_("Modificada Fecha Última Sincronización") +
                " %s: %s a %s" % (rec.name, last_value.get(rec.id), rec.last_sync))

        return res

    def paybook_get_transactions(self, dt_param=False, force_dt=False):
        self.ensure_one()
        dt_param = dt_param or 'dt_transaction_from'

        force_dt = force_dt.date() if force_dt else False
        last_sync = force_dt or self.last_sync

        # Si hay una fecha maximo historica tomar esto como limite para no traer transacciones mas viejas y evitar
        # traernos transacciones duplicadas. Esto para el tema cuando cambia el usuario pero hacen referencia a la misma
        # cuenta y transacciones pra evitar duplicados.
        max_date = self.account_online_link_id.paybook_max_date
        if max_date and last_sync < max_date:
            last_sync = max_date

        last_sync = datetime.combine(last_sync, datetime.min.time())
        params = {'id_credential': self.account_online_link_id.client_id,
                  'id_account': self.online_identifier,
                  dt_param: last_sync.strftime('%s')}

        response = self.account_online_link_id._paybook_fetch('GET', '/transactions', params=params)
        transactions = []
        for trx in response:

            if dt_param == 'dt_transaction_from':
                if trx.get('is_pending') or trx.get('is_disable') or trx.get('is_deleted'):
                    continue

            # save information if the tx has been deleted/disabled or refreshed
            transaction_type = tx_update_dt = ''

            if trx.get('dt_deleted'):
                transaction_type = 'deleted'
                tx_update_dt = trx.get('dt_deleted')
            elif trx.get('dt_disable'):
                transaction_type = 'disable'
                tx_update_dt = trx.get('dt_disable')
            elif trx.get('dt_refresh') and trx.get('dt_refresh') != trx.get('dt_transaction'):
                transaction_type = 'refreshed'
                tx_update_dt = trx.get('dt_refresh')
            elif trx.get('is_pending'):
                transaction_type = 'pending'

            trx_data = {
                'date': datetime.fromtimestamp(trx.get('dt_transaction')).date(),
                'online_transaction_identifier': trx.get('id_transaction'),
                'payment_ref': trx.get('description'),
                'amount': trx.get('amount'),
                # 'end_amount': self.balance,
                'ref': trx.get('reference') or '',
                'transaction_type': transaction_type,
                'narration': '' if not tx_update_dt else
                transaction_type + ' ' + datetime.fromtimestamp(tx_update_dt).date().strftime('%Y/%m/%d'),
            }

            extra_data = trx.get('extra')
            if extra_data:
                self._update_with_value(trx_data, 'sequence', extra_data.get('order'))
                self._update_with_value(trx_data, 'payment_ref', extra_data.get('caption'))
                self._update_with_value(trx_data, 'payment_ref', extra_data.get('caption2'))
                self._update_with_value(trx_data, 'payment_ref', extra_data.get('caption3'))
                self._update_with_value(trx_data, 'payment_ref', extra_data.get('caption4'))
                self._update_with_value(trx_data, 'payment_ref', extra_data.get('voucher_number'))
                self._update_with_value(trx_data, 'payment_ref', extra_data.get('group_of_concept'))
                self._update_with_value(trx_data, 'payment_ref', extra_data.get('terminal_number'))

                # Used to improve name for Banco BIND (AR)
                self._update_with_value(trx_data, 'payment_ref', extra_data.get('spei_beneficiary_tax_id'))
                self._update_with_value(trx_data, 'payment_ref', extra_data.get('spei_beneficiary_name'))
                self._update_with_value(trx_data, 'payment_ref', extra_data.get('spei_concept'))

                # We are appending the reference to the name. This will be repeated data but it will
                # be an improve in the bank statement wizard. The wizard only show the name of the
                # statement line. does not show the reference and we needed so the user can easily
                # check anything to make the reconcile.
                if trx_data.get('ref') not in trx_data.get('payment_ref'):
                    self._update_with_value(trx_data, 'payment_ref', trx_data.get('ref'))

            transactions.append(trx_data)
        return transactions

    def retrieve_refreshed_transactions(self, force_dt):
        """ Try to update Odoo statement line that has been refreshed, disable or deleted on the provider side

        * update refreshed info in Odoo that are informative and safe
        * delete transactions that has been marked as disabled or deleted (if not reconciled)
        * add notification in the statement for the user that have transactions that has been disable/deleted and
          that has been already reconciled this way he can reviewed them and proper unreconcile / reconcile them """
        if not self.journal_ids:
            return 0

        transactions = self.paybook_get_transactions(dt_param='dt_refresh_from', force_dt=force_dt)

        all_lines = self.env['account.bank.statement.line'].search([
            ('journal_id', '=', self.journal_ids.id),
            ('date', '>=', force_dt)])

        txs_to_update = self.env['account.bank.statement.line']
        tx_count = 0
        for tx_raw in transactions:
            tx = all_lines.search([('online_transaction_identifier', '=', tx_raw['online_transaction_identifier'])])
            # Si la tx esta en Odoo
            if tx:
                # Si ha sido marcada como deshabilitada o ha sido eliminada en paybook
                if tx_raw['transaction_type'] in ['deleted', 'disable']:
                    # Si ha sido conciliada marcar y avisar se debe revisar y desconciliar en el chatter del extracto
                    if tx.journal_entry_ids:
                        txs_to_update += tx
                    else:  # Si no ha sido conciliada entonces borrar directamente.
                        tx.unlink()
                else:
                    # Ha sido refrescada la info debemos actualizar los datos en Odoo
                    # Si ya fue conciliada actualizamos solo valores informativos/seguros, no actualizamos los campos
                    # amount/end_amount
                    if tx.journal_entry_ids:
                        tx_raw.pop('amount')

                    # No modificamos la fecha ni el importe de las transacciones más antiguas que una semana,
                    # independientemente si tiene extractos diarios, semanales o mensuales y si las transacciones están
                    # conciliadas o no. Esto porque nos estamos trayendo errores raros de paybook que estamos intentado
                    # evitar
                    if tx.date < force_dt.date():
                        tx_raw.pop('date')
                        tx_raw.pop('amount', False)

                    # TODO Si cambia la fecha deberiamos reubicar la linea en el extracto que corresponda. Tener en
                    # cuenta la config de agrupamiento del diario. Creo que ya hay un metodo que nos puede ayudar a
                    # calcular esto.

                # tx_raw.pop('end_amount')
                if tx.exists():
                    tx.write(tx_raw)
                tx_count += 1

        if txs_to_update:
            statement_ids = txs_to_update.mapped('statement_id')
            for st in statement_ids:
                st.message_post(
                    body=_(
                        'These transactions have been deleted or disable by the bank provider,'
                        ' please review them and if needed unreconcile them, delete them and try to reconcile with'
                        ' the proper bank statement line. You can check this in action menu "Find possible duplicates"') + ' <ul>%s</ul>' % (
                            ''.join([
                                '<li><a href=# data-oe-model=account.bank.statement.line data-oe-id=%d>%s</a></li>' % (
                                    item.id, item.name)
                                for item in txs_to_update.filtered(lambda x: x.statement_id == st)
                            ])
                    ),
                    subtype="mail.mt_comment")
        return tx_count
