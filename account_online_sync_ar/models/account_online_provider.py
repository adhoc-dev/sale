# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import UserError
from odoo.tools import date_utils
from datetime import datetime
from datetime import timedelta
import json
import werkzeug
import requests
import uuid
import logging

_logger = logging.getLogger(__name__)


class PaybookProviderAccount(models.Model):

    _inherit = ['account.online.provider']

    provider_type = fields.Selection(selection_add=[('paybook', 'Paybook')])
    next_refresh = fields.Datetime("Odoo Cron Next synchronization")
    paybook_next_refresh = fields.Datetime("Next synchronization")

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

    def update_credentials(self):
        journal_id = self.account_online_journal_ids.mapped('journal_ids.id')
        journal_id = journal_id[0] if len(journal_id) >= 1 else False
        return self.with_context(journal_id=journal_id)._paybook_open_login()

    def unlink(self):
        """ once the user has deleted the provider remove the date from paybook"""
        paybook_providers = self.filtered(lambda x: x.provider_type == 'paybook')
        for provider in paybook_providers:
            provider._paybook_fetch('DELETE', '/credentials/' + provider.provider_account_identifier, {}, {})
        return super().unlink()

    @api.model
    def _paybook_get_user_token(self, company):
        """ Get the user token saved in the company, if this one is a valid one return it, if not create a new token """
        data = {"id_user": company.paybook_user_id}
        response = self._paybook_fetch('POST', '/sessions', {}, data, 'api_key')
        _logger.info("New paybook token created: %s" % response.get('token'))
        return response.get('token')

    @api.model
    def _paybook_register_new_user(self, company):
        data = {'name': self.env.registry.db_name + '_' + str(uuid.uuid4())}
        if company.paybook_user_id:
            raise UserError(_('You already have a pyabook user'))
        else:
            response = self._paybook_fetch('POST', '/users', {}, data, 'api_key')
            company.paybook_user_id = response.get('id_user')

    @api.model
    def _paybook_open_login(self):
        company = self.env.company
        if not company.sudo().paybook_api_key:
            raise UserError(_('There is not API KEY configure, we can not generate new token'))
        if not company.paybook_user_id:
            self._paybook_register_new_user(company)
        journal_id = self.env.context.get('journal_id') or 0
        return {'type': 'ir.actions.act_url', 'target': 'self',
                'url': '/account_online_sync_ar/configure_paybook/%s/%s' % (company.id, journal_id)}

    @api.model
    def _paybook_fetch(self, method, url, params, data, auth='token', response_status=False, raise_status=True):
        base_url = 'https://sync.paybook.com/v1'
        company = self.company_id if self else self.env.company
        if not company.sudo().paybook_api_key:
            raise UserError(_('There is not API KEY configure, we can not generate new token'))
        if not company.paybook_user_id and url != '/users':
            self._paybook_register_new_user(company)

        parsed_data = ""
        if not url.startswith(base_url):
            url = base_url + url

        headers = {"Authorization": "TOKEN token=" + self._paybook_get_user_token(company)
                   if auth == 'token' else "API_KEY api_key=" + company.sudo().paybook_api_key}
        error = response = False
        try:
            if data:
                parsed_data = json.dumps(data)
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
    def _paybook_get_credentials(self, company, id_credential, account_info=None, account_values=None):
        """ Get credentials in order to create a new online.provider or update an exist ones """

        response = self._paybook_fetch('GET', '/credentials/' + id_credential, {}, {}, response_status=True,
                                       raise_status=False)
        credential = response.get('response')[0]

        # The credential has not been sync, force to sync
        if not credential.get('dt_ready') and credential.get('ready_in') == 0:
            self._paybook_fetch('PUT', '/credentials/' + id_credential + '/sync', {}, {}, response_status=True)
            response = self._paybook_fetch('GET', '/credentials/' + id_credential, {}, {}, response_status=True,
                                           raise_status=False)
            credential = response.get('response')[0]

        next_refresh = credential.get('dt_ready')
        last_refresh = credential.get('dt_refresh')
        last_refresh_tomorrow = date_utils.add(datetime.fromtimestamp(last_refresh), days=1)
        values = {}

        if account_info and account_values:
            values = {
                'name': _('Paybook') + ' ' + account_info[0].get('site', {}).get('name'),
                'account_online_journal_ids': account_values,
                'provider_type': 'paybook',
                'provider_account_identifier': id_credential,
                'provider_identifier': credential.get('id_site'),
                'company_id': company.id,  # TODO review if really needed"
            }
        values.update({
            'last_refresh': datetime.fromtimestamp(last_refresh) if last_refresh else False,
            'paybook_next_refresh': datetime.fromtimestamp(next_refresh) if next_refresh else last_refresh_tomorrow,
        })

        response.update({'code': credential.get('code')})
        values.update(self._paybook_check_credentials_response(response))
        return values

    @api.model
    def _paybook_success(self, credential_data):
        """ Get info about account, Create online journal account, Create provider online account """
        yesterday = date_utils.subtract(fields.Date.today(), days=1)
        company = self.env['res.company'].browse(int(credential_data.get('company_id')))
        journal_id = int(credential_data.get('journal_id') or False)
        journal = self.env['account.journal'].browse(int(journal_id)) if journal_id else False
        id_credential = credential_data.get('id_credential')

        # Get info about accounts
        params = {'id_credential': id_credential}
        account_info = self._paybook_fetch('GET', '/accounts', params, {}, raise_status=False)

        # Check if provider already exist
        provider_account = self.search([('provider_account_identifier', '=', id_credential)])

        # Prepare info of accounts for Odoo
        account_values = []
        for acc in account_info:
            online_account = provider_account.account_online_journal_ids.filtered(
                lambda x: x.online_identifier == acc.get('id_account'))
            if online_account:
                account_values.append((1, online_account.id, {
                    'balance': acc.get('balance', 0),
                    'last_sync': datetime.fromtimestamp(acc.get('dt_refresh')) if acc.get('dt_refresh') else yesterday,
                }))
            else:
                account_values.append((0, 0, {
                    'name': acc.get('site', {}).get('name') + ': ' + acc.get('name') + ' Nro. ' + acc.get('number'),
                    'account_number': acc.get('number'),
                    'online_identifier': acc.get('id_account'),
                    'balance': acc.get('balance', 0),
                    'journal_ids': [(4, journal.id)] if journal and len(account_info) == 1 else False,
                    'last_sync': datetime.fromtimestamp(acc.get('dt_refresh')) if acc.get('dt_refresh') else yesterday,
                }))

        # Extract online provider info
        values = self._paybook_get_credentials(company, id_credential, account_info, account_values)

        if provider_account:
            provider_account.sudo().write(values)
            method = 'edit'
        else:
            provider_account = self.create(values)
            method = 'add' if journal else 'edit'

        res = {'status': provider_account.status, 'message': provider_account.message, 'method': method,
               'added': provider_account.account_online_journal_ids.filtered(lambda x: not x.journal_ids)}

        if journal:
            res['journal_id'] = journal.id

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
        error_code = response.get('code')
        hint_message = ''
        if error_code:
            hint_message = self._paybook_get_error_from_code(error_code)

        ready_in = response.get('response')[0].get('ready_in')
        ready_in_msg = '\n' + _('The next transactions sync will be available in %s hours') % str(
            timedelta(seconds=ready_in)) if ready_in else ''

        return {
            'status': 'FAILED' if error_code >= 400 else 'SUCCESS',
            'status_code': error_code,
            'message': (response.get('message') or '') + hint_message + ready_in_msg,
            'action_required': error_code >= 400,
        }

    @api.model
    def _paybook_get_error_from_code(self, code):
        return {
            # 1xx Progress Information Codes
            '100': _('Register - The API registers a new process (through a REST request)'),
            '101': _('Starting - The process information was obtained to start operating'),
            '102': _('Running - The process is running (login successful)'),
            '103': _('TokenReceived - The process received the token'),

            # 2xx Success Codes
            '200': _('Finish - The connection has been successful. Data has been extracted'),
            '201': _('Pending - The connection has been successful. We have partially extracted information but data'
                     ' will still be extracted in background processes.'),
            '202': _('NoTransactions - The connection has been successful. However, no transactions were found.'),
            '203': _('PartialTransactions - The connection has been successful. However, more than one account does not'
                     ' have transactions.'),
            '204': _('Incomplete - The connection has been successful. However, the data downloaded is incompleted.'),
            '206': _('NoAccounts - The connection has been successful. However, there were no accounts linked to the '
                     'given credentials.'),

            # 4xx User Interaction Codes
            '400': _('Bad Request.'),
            '401': _('Unauthorized - The value of one of the given Authentication Fields was not accepted by the '
                     'institution. Please verify the information and try again.'),
            '402': _('Payment Required'),
            '403': _('Forbidden or Invalidtoken - The given token value introduced was not accepted by the institution'
                     ' or the expiration time was reached.'),
            '404': _('Not Found.'),
            '405': _('Locked - The institution has blocked the given credential, please contact your institution and '
                     'make sure your connection to the site is working properly before trying again.'),
            '406': _('Conflict - The institution does not allow to have more than one user logged in. If you have '
                     'logged in to your institution using another device, please make sure to log out before trying'
                     ' again.'),
            '408': _('UserAction - The institution requires attention from the user. We advise you to log in to the '
                     'institution to confirm everything is working properly. Upon confirmation, try again.'),
            '409': _('WrongSite - The given credentials seem to be valid but they belong to a different site from the '
                     'same organization.'),
            '429': _('Too Many Requests.'),

            # 4xx Multi-Factor Authentication Codes
            '410': _('Waiting - Waiting for MFA Value'),
            '411': _('TwofaTimeout - The time to introduce the MFA value has been exceeded.'),
            '413': _('LoginError - There is a error in Login Process, please try again.'),

            #  5xx Connection Error Codes
            '500': _('Error - An internal error has been ocurred while connecting to the institution'),
            '501': _('Unavailable - The instituion has informed to us that there was a problem in the connection. '
                     'Please wait 15 minutes and try again. If the problem persists contact Technical Support.'),
            '503': _('Service Unavailable.'),
            '504': _('ConnectionTimeout - An internal error has been ocurred while connecting to the institution.'),
            '509': _('UndergoingMaintenance - The institution is under maintenance.'),
        }.get(str(code), _('An error has occurred (code %s)' % code))
