# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import UserError
from odoo.tools import date_utils
from datetime import datetime
from datetime import timedelta
import json
import werkzeug
import requests
import logging
import time

_logger = logging.getLogger(__name__)


class PaybookProviderAccount(models.Model):

    _inherit = ['account.online.provider']

    provider_type = fields.Selection(selection_add=[('paybook', 'Paybook')])
    # Only rename this field to avoid confusions
    next_refresh = fields.Datetime("Odoo cron next run")
    paybook_next_refresh = fields.Datetime("Next transactions will be available at")

    def _get_available_providers(self):
        ret = super()._get_available_providers()
        ret.append('paybook')
        return ret

    def manual_sync(self):
        if self.provider_type != 'paybook':
            return super().manual_sync()
        self.ensure_one()
        transactions = []
        for account in self.account_online_journal_ids:
            if account.journal_ids:
                trx_count = account.retrieve_transactions()
                transactions.append({'journal': account.journal_ids[0].name, 'count': trx_count})

        values = self._paybook_get_credentials(self.company_id, self.provider_account_identifier)
        self.sudo().write(values)

        result = {'status': self.status, 'message': self.message, 'transactions': transactions, 'method': 'refresh',
                  'added': self.env['account.online.journal']}
        return self.show_result(result)

    @api.model
    def cron_fetch_online_transactions(self):
        if self.provider_type != 'paybook':
            return super().cron_fetch_online_transactions()
        if self.status == 'SUCCESS':
            self.manual_sync()
            # TODO KZ only do the manual sync if the paybook next date is less than the current one
            # paybook_next_refresh

    def update_credentials(self):
        journal_id = self.account_online_journal_ids.mapped('journal_ids.id')
        journal_id = journal_id[0] if len(journal_id) >= 1 else False
        return self.with_context(journal_id=journal_id)._paybook_open_update_credential()

    def online_account_delete_credentials(self):
        """ Let to delete credential form paybook and also remove info from odoo online provider """
        paybook_providers = self.filtered(lambda x: x.provider_type == 'paybook')
        for provider in paybook_providers:
            if not provider.provider_account_identifier:
                raise UserError(_('There is not account credential to be deleted'))
            provider._paybook_fetch('DELETE', '/credentials/' + provider.provider_account_identifier)
            provider.provider_account_identifier = False

    @api.model
    def _paybook_open_login(self):
        journal_id = self.env.context.get('journal_id') or 0
        company = self.env['account.journal'].browse(journal_id).company_id if journal_id else self.env.company
        if not company.paybook_user_id:
            company._paybook_register_new_user()
        return {'type': 'ir.actions.act_url', 'target': 'self',
                'url': '/account_online_sync_ar/configure_paybook/%s/%s' % (company.id, journal_id)}

    @api.model
    def _paybook_open_update_credential(self):
        """ Display the widget to let the user update a bank password, it will open directly
        the bank page to be modified """
        journal_id = self.env.context.get('journal_id') or 0
        company = self.env['account.journal'].browse(journal_id).company_id if journal_id else self.env.company
        if not company.paybook_user_id:
            company._paybook_register_new_user()
        return {'type': 'ir.actions.act_url', 'target': 'self',
                'url': '/account_online_sync_ar/update_bank/%s/%s/%s' % (company.id, journal_id, self.id)}

    def _paybook_fetch(self, method, url, params={}, data={}, response_status=False, raise_status=True):
        base_url = 'https://sync.paybook.com/v1'
        if self:
            company = self.company_id
        else:
            company_id = self.env.context.get('paybook_company_id')
            company = self.env['res.company'].browse(company_id) if company_id else self.env.company

        if not company.paybook_user_id:
            company._paybook_register_new_user()

        parsed_data = ""
        if not url.startswith(base_url):
            url = base_url + url

        headers = {"Authorization": "TOKEN token=" + company._paybook_get_user_token()}
        error = response = False
        try:
            if data:
                parsed_data = json.dumps(data)
            _logger.info('%s %s, params=%s, data=%s, headers=%s' % (method, url, params, parsed_data, headers))
            raw_response = requests.request(method=method, url=url, params=params, data=parsed_data, headers=headers,
                                            timeout=60)
            response = raw_response.json()
            if response.get('errors') or response.get('code') != 200:
                error = response
                # TODO improve error process. review error codes and do what is needed here
                # self._paybook_update_status('FAILED', resp_json)
                # Manage errors and get new token if needed
        except requests.exceptions.Timeout:
            raise UserError(_('Timeout: the server did not reply within 60s'))
        except requests.exceptions.ConnectionError:
            raise UserError(_('Server not reachable, please try again later'))
        except Exception as exception:
            raise UserError(_('Unknown exception %s') % repr(exception))
        if error:
            if raise_status:
                raise UserError(_(
                    "Paybook fetch: Please comunicate with your Odoo Provider. This is what we got %s" % repr(error)))
            return response
        return response if response_status else response.get('response')

    @api.model
    def _paybook_get_credentials(self, company, id_credential):
        """ Get data dictionary in order to create a new online.provider or update an exist one.
        This method will do a call to GET /credentials to get the credentials info.

        This method is called from two places:
        * when the credential is added
        * when we do a syncronization of the transactions.
        """
        response = self._paybook_fetch('GET', '/credentials/' + id_credential, response_status=True, raise_status=False)
        cred = response.get('response')[0]
        id_site = cred.get('id_site')
        values = {
            'name': self.get_bank_name(id_site),
            'provider_type': 'paybook',
            'provider_account_identifier': id_credential,
            'company_id': company.id,  # TODO review if really needed"
            'provider_identifier': id_site,

            # dt_refresh disponible en cred y acc. es la fecha de la ultima transaccion sincronizada
            'last_refresh': datetime.fromtimestamp(cred.get('dt_refresh')) if cred.get('dt_refresh')
            else False,

            # dt_ready indica la fecha en la cuál se puede volver a ejecutar una credencial sin obtener error 429
            'paybook_next_refresh': datetime.fromtimestamp(cred.get('dt_ready')) if cred.get('dt_ready')
            else False,
        }
        values.update(self._paybook_check_credentials_response(response))
        return values

    def action_paybook_force_sync(self):
        """ This method will try to make a request to syncfy to force the update of the available transactions in order
        to try to sync new transactions from the bank """
        id_credential = self.provider_account_identifier
        _logger.info('Syncfy Try force credential sync')
        response = self._paybook_fetch('GET', '/credentials/' + id_credential, response_status=True, raise_status=False)
        cred = response.get('response')[0]
        # The credential has not error byt has not been sync, force to sync
        if cred.get('code') < 400 and not cred.get('dt_ready') and cred.get('ready_in') == 0:
            self._paybook_fetch('PUT', '/credentials/' + id_credential + '/sync')
            # cred = self._paybook_fetch('GET', '/credentials/' + id_credential, raise_status=False)

    @api.model
    def _update_cred_response(self, credential_data):
        """ method that receive the response of the update credential widget and prepare the data to b show to odoo if the credential was successfully updated or it has been
        any problem """
        company = self.env['res.company'].browse(int(credential_data.get('company_id')))
        id_credential = credential_data.get('id_credential')

        provider_account = self.search([('provider_account_identifier', '=', id_credential)])
        values = self.with_context(paybook_company_id=company.id)._paybook_get_credentials(company, id_credential)

        everything_ok = credential_data['state'] == 'success' and values['status_code'] < 400

        res = {'status': 'SUCCESS' if everything_ok else 'FAILED',
               'message': 'Se actualizo las credenciales del banco' if everything_ok else values['message'],
               'method': 'refresh'}

        url = '/web#model=account.online.wizard&id=%s&action=account_online_sync.action_account_online_wizard_form'
        action = provider_account.show_result(res)
        return werkzeug.utils.redirect(url % action.get('res_id'))

    @api.model
    def _paybook_success(self, credential_data):
        """ Get info about account, Create online journal account, Create provider online account """
        company = self.env['res.company'].browse(int(credential_data.get('company_id')))
        journal_id = int(credential_data.get('journal_id') or False)
        journal = self.env['account.journal'].browse(int(journal_id)) if journal_id else False
        id_credential = credential_data.get('id_credential')

        # Check if provider already exist
        provider_account = self.search([('provider_account_identifier', '=', id_credential)])

        # Extract online provider info
        values = self.with_context(paybook_company_id=company.id)._paybook_get_credentials(company, id_credential)

        # Get Account Data
        account_values = provider_account._get_account_values(credential_data)
        if account_values:
            values.update({'account_online_journal_ids': account_values})

        if provider_account:
            prev_accounts = provider_account.account_online_journal_ids
            provider_account.sudo().write(values)
            method = 'edit'
            added = provider_account.account_online_journal_ids - prev_accounts.filtered(lambda x: x.journal_ids)
        else:
            provider_account = self.create(values)
            method = 'add' if journal else 'edit'
            added = provider_account.account_online_journal_ids

        res = {'status': provider_account.status, 'message': provider_account.message, 'method': method,
               'added': added}

        if journal:
            res['journal_id'] = journal.id

        if not account_values:
            res = {'status': 'FAILED',
                   'message': provider_account.message + '\nNo se pudieron sincronizar las cuentas intentar nuevamente',
                   'method': method, 'added': added}

        url = '/web#model=account.online.wizard&id=%s&action=account_online_sync.action_account_online_wizard_form'
        action = provider_account.show_result(res)
        return werkzeug.utils.redirect(url % action.get('res_id'))

    def _paybook_update_status(self, response):
        """ Update the provider status """
        self.write(self._paybook_check_credentials_response(response))
        return True

    @api.model
    def _paybook_check_credentials_response(self, response):
        """ review response and return values to be use for provider status """
        response_code = response.get('response')[0].get('code')
        hint_message = ''
        if response_code:
            hint_message = self._paybook_get_error_from_code(response_code)

        ready_in = response.get('response')[0].get('ready_in')
        ready_in_msg = '\n' + _('The next transactions sync will be available in %s hours') % str(
            timedelta(seconds=ready_in)) if ready_in else ''

        return {
            'status': 'FAILED' if response_code >= 400 else 'SUCCESS',
            'status_code': response_code,
            'message': (response.get('message') or '') + hint_message + ready_in_msg,
            'action_required': response_code >= 400,
        }

    @api.model
    def _paybook_get_error_from_code(self, code):
        return {
            # 1xx Progress Information Codes
            '100': _('100: Register - The API registers a new process (through a REST request)'),
            '101': _('101: Starting - The process information was obtained to start operating'),
            '102': _('102: Running - The process is running (login successful)'),
            '103': _('103: TokenReceived - The process received the token'),

            # 2xx Success Codes
            '200': _('200: Finish - The connection has been successful. Data has been extracted'),
            '201': _('201: Pending - The connection has been successful. We have partially extracted information but'
                     ' data will still be extracted in background processes.'),
            '202': _('202: NoTransactions - The connection has been successful. However, no transactions were found.'),
            '203': _('203: PartialTransactions - The connection has been successful. However, more than one account'
                     ' does not have transactions.'),
            '204': _('204: Incomplete - The connection has been successful. However, the data downloaded is'
                     ' incompleted.'),
            '206': _('206: NoAccounts - The connection has been successful. However, there were no accounts linked to'
                     ' the given credentials.'),

            # 4xx User Interaction Codes
            '400': _('400: Bad Request.'),
            '401': _('401: Unauthorized - The value of one of the given Authentication Fields was not accepted by the '
                     'institution. Please verify the information and try again.'),
            '402': _('402: Payment Required'),
            '403': _('403: Forbidden or Invalidtoken - The given token value introduced was not accepted by the '
                     'institution or the expiration time was reached.'),
            '404': _('404: Not Found.'),
            '405': _('405: Locked - The institution has blocked the given credential, please contact your institution'
                     ' and make sure your connection to the site is working properly before trying again.'),
            '406': _('406: Conflict - The institution does not allow to have more than one user logged in. If you have '
                     'logged in to your institution using another device, please make sure to log out before trying'
                     ' again.'),
            '408': _('408: UserAction - The institution requires attention from the user. We advise you to log in to'
                     ' the institution to confirm everything is working properly. Upon confirmation, try again.'),
            '409': _('409: WrongSite - The given credentials seem to be valid but they belong to a different site from'
                     ' the same organization.'),
            '429': _('429: Too Many Requests.'),

            # 4xx Multi-Factor Authentication Codes
            '410': _('410: Waiting - Waiting for MFA Value'),
            '411': _('411: TwofaTimeout - The time to introduce the MFA value has been exceeded.'),
            '413': _('413: LoginError - There is a error in Login Process, please try again.'),

            #  5xx Connection Error Codes
            '500': _('500: Error - An internal error has been ocurred while connecting to the institution'),
            '501': _('501: Unavailable - The instituion has informed to us that there was a problem in the connection.'
                     ' Please wait 15 minutes and try again. If the problem persists contact Technical Support.'),
            '503': _('503: Service Unavailable.'),
            '504': _('504: ConnectionTimeout - An internal error has been ocurred while connecting to the'
                     ' institution.'),
            '509': _('509: UndergoingMaintenance - The institution is under maintenance.'),
        }.get(str(code), _('An error has occurred (code %s)' % code))

    def _get_account_values(self, credential_data={}):
        if credential_data:
            company = self.env['res.company'].browse(int(credential_data.get('company_id')))
            id_credential = credential_data.get('id_credential')
        else:
            company = self.company_id
            id_credential = self.provider_account_identifier

        journal_id = int(credential_data.get('journal_id') or False)
        journal = self.env['account.journal'].browse(int(journal_id)) if journal_id else False

        # Get info about accounts
        account_info = self.with_context(paybook_company_id=company.id)._paybook_fetch(
            'GET', '/accounts?id_credential=' + str(id_credential), raise_status=False)

        # After create the credential if we consult the accounts maybe the accounts info is not available, we can wait
        # one minute in order to wait for the account_info.
        if not account_info:
            _logger.info('Waiting 60 seconds to get account info')
            time.sleep(60)
            account_info = self.with_context(paybook_company_id=company.id)._paybook_fetch(
                'GET', '/accounts?id_credential=' + str(id_credential), raise_status=False)

        # Prepare info of accounts for Odoo
        account_values = []
        for acc in account_info:
            online_account = self.account_online_journal_ids.filtered(
                lambda x: x.online_identifier == acc.get('id_account'))
            if online_account:
                account_values.append((1, online_account.id, {
                    'balance': acc.get('balance', 0),
                    'last_sync': datetime.fromtimestamp(acc.get('dt_refresh')) if acc.get('dt_refresh') else False,
                }))
            else:
                account_values.append((0, 0, {
                    'name': acc.get('site', {}).get('name') + ': ' + acc.get('name') +
                    (' Nro. ' + acc.get('number') if acc.get('number') else ''),
                    'account_number': acc.get('number'),
                    'online_identifier': acc.get('id_account'),
                    'balance': acc.get('balance', 0),
                    'journal_ids': [(4, journal.id)] if journal and len(account_info) == 1 else False,
                    'last_sync': datetime.fromtimestamp(acc.get('dt_refresh')) if acc.get('dt_refresh') else False,
                }))
        return account_values

    @api.model
    def get_bank_name(self, id_site):
        """ this value we get it from the GET credential and with this we can now the bank site where the credentials
        belongs """
        data = {
            '5941dd12056f29061d344ca1': 'Patagonia ebank Empresas',
            '5980bb94056f292f433f0cd1': 'Banco Ciudad Empresas',
            '59d2a397056f2925b252b982': 'BBVA Francés Net Cash',
            '5a3da41e056f2905c6245d61': 'Banco Credicoop',
            '5b0d8d1d056f2924ea7a2fb2': 'Santander Rio',
            '5f0c5ef8479b243d4d67e611': 'Santander Rio Personal',
            '5f0c5ef8479b243d4d67e612': 'Santander Rio Personal Select',
            '5b566e0d7d8b6b0628564cf2': 'Banco Galicia Negocios',
            '5be9c00b7d8b6b643726a300': 'Banco Galicia Personal',
            '5c23bc89f9de2a1a022f0e52': 'Banco Macro Empresas',
            '5f2dc493fd79f92aec276c01': 'Banco Macro Empresas Nuevo',
            '5c3f82a4f9de2a08177b2d42': 'ICBC Empresas',
            '5c7b6035f9de2a087b355c82': 'Banco Comafi Empresas',
            '5d1ce9a6f9de2a07ed574492': 'Banco Provincia Empresas',
            '5d430ba4f9de2a07fb58d612': 'Banco Supervielle Empresas',
            '5d77c3fbf9de2a08f33d9032': 'Banco Nacion Empresas',
            '5e2626c89be72331726b8502': 'Banco de Córdoba Empresas',

            # Really not used at the moment
            "60e72485510da807ddd7c89a": "Mercado Pago",
            '5c65e306f9de2a080b61bb32': 'AFIP Alta usuario',
            '5cf9816af9de2a7ae11c2981': 'AFIP Mis Comprobantes',
            '5e18e47942eccb2dc5247ce1': 'AFIP Aceptar Relaciones',

        }
        return data.get(id_site, 'Banco/Monedero no encontrado')
