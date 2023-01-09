from odoo import models, api, fields, _
from odoo.exceptions import UserError
from odoo.tools import date_utils
from odoo.tools.safe_eval import safe_eval
from datetime import datetime
from datetime import timedelta
import json
import werkzeug
import requests
import logging
import time

_logger = logging.getLogger(__name__)


class AccountOnlineLink(models.Model):

    _inherit = ['account.online.link']

    provider_type = fields.Selection([('paybook', 'Synfcy'), ('saltedge', 'Odoo')], 'Proveedor')

    # Only rename this field to avoid confusions
    next_refresh = fields.Datetime("Oodo Cron Next Run")

    paybook_username_hint = fields.Char("Login/User")
    client_id = fields.Char(tracking=True)

    paybook_max_date = fields.Date(
        "Fecha tope sincronización", help="Si esta configurada indica la fecha tope hacia atrás en la cual se puede"
        " hacer sincronización con esta credencial. Esto sirve por:\n * Si se tuvo que reemplazar la credencial debido"
        " a que cambio el username evitar ids duplicados.\n * Si hicieron carga manual de algun dia y quieren"
        " sincronizar a partir del dia siguiente", tracking=True)

    auto_sync = fields.Boolean(tracking=True)
    paybook_refresh_days = fields.Integer("Last Days to be Updated/fixed", compute="_compute_paybook_refresh_days")

    # Este estaba en el viejo sync y lo necesitamos para almacenar el error recibido por paybook
    status_code = fields.Char(readonly=True, help='Code to identify problem')
    message = fields.Char(readonly=True, help='Techhnical message from third party provider that can help debugging')
    action_required = fields.Boolean(readonly=True, help='True if user needs to take action by updating account', default=False)
    provider_identifier = fields.Char(readonly=True, help='ID of the banking institution in third party server used for debugging purpose')

    def _compute_paybook_refresh_days(self):
        self.paybook_refresh_days = int(self.env['ir.config_parameter'].sudo().get_param('account_online_sync_ar.update_last_days', "7"))

    def action_paybook_update_transactions(self):
        """ This method will review if there is refreshed transactions and will update its values on Odoo """
        self.ensure_one()
        transactions = []
        fix_days = int(self.env['ir.config_parameter'].sudo().get_param('account_online_sync_ar.update_last_days', "7"))
        for account in self.account_online_account_ids:
            if account.journal_ids:
                force_dt = fields.Datetime.today() - timedelta(days=fix_days)
                trx_count = account.retrieve_refreshed_transactions(force_dt=force_dt)
                transactions.append({'journal': account.journal_ids[0].name, 'count': trx_count})

        values = self._paybook_get_credentials(self.company_id, self.client_id)
        self.sudo().write(values)

        result = {'status': self.state, 'message': _("Actualizar transacciones existentes: ") + self.message,
                  'transactions': transactions, 'method': 'refresh', 'added': self.env['account.online.account']}
        return self.show_result(result)

    def show_result(self, result):
        """ Mensaje escribiendo resultado de conexión a paybook dice que se hizo y el mensaje y codigo de respuesta
        asociado """
        self.ensure_one()
        msg = _("<b>%s</b> - <i>%s</i>") % (result.get('status').upper(), result.get('message'))
        added = result.get('added')
        if added:
            msg += _("<i>. Fueron agregados %s registros</i>") % (added)
        self.message_post(body=msg)

    def action_update_credentials(self):
        """ Extender para abrir widget de paybook asi actualizar la contraseña dedse alli """
        if self.provider_type != 'paybook':
            return super().action_update_credentials()
        self.ensure_one()
        return self._paybook_open_update_credential()

    def online_account_delete_credentials(self):
        """ Let to delete credential form paybook and also remove info from odoo online provider """
        paybook_providers = self.filtered(lambda x: x.provider_type == 'paybook')
        for provider in paybook_providers:
            if not provider.client_id:
                raise UserError(_('There is not account credential to be deleted'))
            provider._paybook_fetch('DELETE', '/credentials/' + provider.client_id)
            provider.client_id = False

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
        self.ensure_one()
        return {'type': 'ir.actions.act_url', 'target': 'self',
                'url': '/account_online_sync_ar/update_bank/%s/%s/%s' % (self.company_id.id, 0, self.id)}

    def _paybook_fetch(self, method, url, params={}, data={}, response_status=False, raise_status=True, external_paybook_id_user=False):
        base_url = 'https://sync.paybook.com/v1'

        if external_paybook_id_user:
            company = self.env['res.company'].search([('paybook_user_id', '=', external_paybook_id_user)])
        else:
            if self:
                company = self.company_id
            else:
                company_id = self.env.context.get('paybook_company_id')
                company = self.env['res.company'].browse(company_id) if company_id else self.env.company

        if not external_paybook_id_user and not company.paybook_user_id:
            company._paybook_register_new_user()

        if not url.startswith(base_url):
            url = base_url + url

        headers = {"Authorization": "TOKEN token=" + company._paybook_get_user_token(id_user=external_paybook_id_user)}
        error = response = False
        try:
            parsed_data = {}
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
            'client_id': id_credential,
            'company_id': company.id,
            'provider_identifier': id_site,
            'paybook_username_hint': cred.get('username'),

            # dt_refresh disponible en cred y acc. es la fecha de la ultima transaccion sincronizada
            'last_refresh': datetime.fromtimestamp(cred.get('dt_refresh')) if cred.get('dt_refresh')
            else False,
        }
        values.update(self._paybook_check_credentials_response(response))
        return values

    def action_paybook_force_sync(self):
        """ This method will try to make a request to syncfy to force the update of the available transactions in order
        to try to sync new transactions from the bank """
        self.ensure_one()
        id_credential = self.client_id
        _logger.info('Syncfy Try force credential sync')
        response = self._paybook_fetch('GET', '/credentials/' + id_credential, response_status=True, raise_status=False)
        cred = response.get('response')[0]
        # The credential has not error byt has not been sync, force to sync
        if cred.get('can_sync') and cred.get('is_authorized') and (cred.get('code') < 400 or cred.get('code') in [406, 408, 500]):
            response = self._paybook_fetch('PUT', '/credentials/' + id_credential + '/sync')
            extra_info = _('Se forzó la sincronizacion bancaria')
            self.message_post(body=extra_info)
            self._fetch_transactions()
        else:
            message = _('No es posible forzar la sincronización. ')
            if cred.get('code') >= 400 and cred.get('code') not in [406, 408, 500]:
                message += _('Solo se pueden forzar credenciales sin estado de error.')
            elif not cred.get('is_authorized'):
                message += _('La credencial no se encuentra autorizada.')
            elif not cred.get('can_sync'):
                dt_ready = fields.Datetime.to_string(fields.Datetime.context_timestamp(self.with_context(tz='America/Buenos_Aires'), \
                            datetime.fromtimestamp(cred.get('dt_ready'))))
                message += _('Ya se ha forzado la sincronización recientemente. Puede intentar nuevamente a las ') + dt_ready
            raise UserError(message)

    def action_initialize_update_accounts(self):
        """ Check the accounts available on the bank and let us to return the information of new accounts.

        This is helpfull also when create a new credential for a new bank that is been integrated and we add the
        accounts in a post process"""
        if self.provider_type != 'paybook':
            return super().action_initialize_update_accounts()

        # Get Account Data and create accounts in Odoo
        self.ensure_one()
        account_values = self._get_account_values()
        if account_values:
            self.sudo().write({'account_online_account_ids': account_values})

        # TODO KZ add a message in the post telling a a new account was created?
        # prev_accounts = self.account_online_account_ids
        # added = self.account_online_account_ids - prev_accounts.sudo().filtered(lambda x: x.journal_ids)
        return self._link_accounts_to_journals_action(self.account_online_account_ids)

    def action_paybook_update_state(self):
        self.ensure_one()
        values = self._paybook_get_credentials(self.company_id, self.client_id)
        self.write(values)
        self.show_result({'status': self.state, 'message': _("Actualizado estado de credencial: ") + self.message})

    @api.model
    def _update_cred_response(self, credential_data):
        """ method that receive the response of the update credential widget and prepare the data to b show to odoo if the credential was successfully updated or it has been
        any problem """
        company = self.env['res.company'].browse(int(credential_data.get('company_id')))
        id_credential = credential_data.get('id_credential')

        provider_account = self.search([('client_id', '=', id_credential)])
        values = self.with_context(paybook_company_id=company.id)._paybook_get_credentials(company, id_credential)

        widget_res = safe_eval(credential_data['result'])
        everything_ok = credential_data['state'] == 'success' and values['status_code'] < 400 and not widget_res['is_new'] and provider_account

        extra_info = ''
        if not everything_ok and (widget_res['is_new'] or not provider_account):
            extra_info = (
                'Creaste una nueva credencial por error o la que intentaste actualizar no existe en esta base de datos.'
                ' Ve al Menu Mi base / Administrar Credenciales y corrige el problema (id_credential: %s).'
                ' Si necesitas ayuda o tienes dudas consulta a ADHOC' % (id_credential))

            _logger.error('Updating a credential %s' % widget_res)
            if provider_account:
                self.message_post(body=extra_info)

        res = {'status': 'connected' if everything_ok else 'error',
               'message': _("Actualizar contraseña del banco: ") + ('Exitoso' if everything_ok else extra_info or values['message']),
               'method': 'refresh'}


        provider_account.show_result(res)
        url = '/web#model=account.online.link&id=%s&view_type=form&action=account_online_synchronization.action_account_online_link_form'
        return werkzeug.utils.redirect(url % provider_account.id)

    @api.model
    def _paybook_success(self, credential_data):
        """ Get info about account, Create online journal account, Create provider online account """
        company = self.env['res.company'].browse(int(credential_data.get('company_id')))
        journal_id = int(credential_data.get('journal_id') or False)
        journal = self.env['account.journal'].browse(int(journal_id)) if journal_id else False
        id_credential = credential_data.get('id_credential')

        # Check if provider already exist
        provider_account = self.search([('client_id', '=', id_credential)])

        # Extract online provider info
        values = self.with_context(paybook_company_id=company.id)._paybook_get_credentials(company, id_credential)

        # Get Account Data
        account_values = provider_account._get_account_values(credential_data)
        if account_values:
            values.update({'account_online_account_ids': account_values})

        if provider_account:
            prev_accounts = provider_account.account_online_account_ids
            provider_account.sudo().write(values)
            method = 'edit'
            added = provider_account.account_online_account_ids - prev_accounts.sudo().filtered(lambda x: x.journal_ids)
        else:
            provider_account = self.create(values)
            method = 'add' if journal else 'edit'
            added = provider_account.account_online_account_ids

        res = {'status': provider_account.state, 'message': provider_account.message, 'method': method,
               'added': added}

        if journal:
            res['journal_id'] = journal.id

        if not account_values:
            res = {'status': 'FAILED',
                   'message': provider_account.message + '\nNo se pudieron sincronizar las cuentas intentar nuevamente',
                   'method': method, 'added': added}

        provider_account.show_result(res)
        action = provider_account._link_accounts_to_journals_action(added)
        url = '/web#model=account.link.journal&id=%s&action=account_online_sync_ar.action_account_link_journal'
        return werkzeug.utils.redirect(url % action.get('res_id'))

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
            'state': 'error' if response_code >= 400 else 'connected',
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
            '501': _('501: Unavailable - The instituion has informed to us that there was a problem in the connection'),
            '503': _('503: Service Unavailable.'),
            '504': _('504: ConnectionTimeout - An internal error has been ocurred while connecting to the'
                     ' institution.'),
            '509': _('509: UndergoingMaintenance - The institution is under maintenance.'),
        }.get(str(code), _('An error has occurred (code %s)' % code))

    def _get_account_values(self, credential_data={}):
        """ devuelve diccionario con los datos para cargar la info de las cuentas en Odoo """
        if credential_data:
            company = self.env['res.company'].browse(int(credential_data.get('company_id')))
            id_credential = credential_data.get('id_credential')
        else:
            company = self.company_id
            id_credential = self.client_id

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
            online_account = self.account_online_account_ids.filtered(
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
    def get_available_banks(self):
        """ Get the list of all available paybook syncfy connections to banks and wallets """
        data = {
            "Argentina": "51ad446b3b8e77631200022a",
            "Uruguay": "51ad44dd3b8e776312000487",
            "Chile": "51ad447b3b8e776312000284",
            "United States": "51ad44db3b8e77631200047d",
        }
        all_site_org = self._paybook_fetch('GET', '/catalogues/site_organizations')
        all_sites = self._paybook_fetch('GET', '/catalogues/sites')

        # Remove AFIP and another Government connections we don't wanted here
        gov_type_id = "56cf4f5b784806cf028b4569"
        all_site_org = [site_org for site_org in all_site_org if site_org.get('id_site_organization_type') != gov_type_id]

        for country_name, id_country in data.items():
            site_organizations = [
                site_org.get('id_site_organization')
                for site_org in all_site_org
                if site_org.get('id_country') == id_country]
            country_sites = [site for site in all_sites if site.get('id_site_organization') in site_organizations]
            data.update({country_name: dict(
                [(site.get('id_site'), site.get('name'))
                 for site in country_sites])})

        # import pprint
        # pprint.pprint(data)
        raise UserError(data)

    @api.model
    def get_bank_name(self, id_site):
        """ when we received id_site from the GET credential we can use this method to now the bank site where the
        credentials belongs. This information can be updated with result of calling the self.get_available_banks()
        method and updating the dictionary on this method.

        NOTE: We create this method to avoid making calls to the syncfy everytime we consult the credential """
        data = {
            # Argentina
            '5941dd12056f29061d344ca1': 'Patagonia ebank Empresas',
            '5980bb94056f292f433f0cd1': 'Banco Ciudad Empresas',
            '59d2a397056f2925b252b982': 'BBVA Francés Net Cash',
            '5a3da41e056f2905c6245d61': 'Banco Credicoop',
            '5b0d8d1d056f2924ea7a2fb2': 'Santander Rio',
            '5b566e0d7d8b6b0628564cf2': 'Banco Galicia Negocios',
            '5be9c00b7d8b6b643726a300': 'Banco Galicia Personal',
            '5c23bc89f9de2a1a022f0e52': 'Banco Macro Empresas',
            '5c3f82a4f9de2a08177b2d42': 'ICBC Empresas',
            '5c7b6035f9de2a087b355c82': 'Banco Comafi Empresas',
            '5d1ce9a6f9de2a07ed574492': 'Banco Provincia Empresas',
            '5d430ba4f9de2a07fb58d612': 'Banco Supervielle Empresas',
            '5d77c3fbf9de2a08f33d9032': 'Banco Nacion Empresas',
            '5e2626c89be72331726b8502': 'Banco de Córdoba Empresas',
            '5f0c5ef8479b243d4d67e611': 'Santander Rio Personal',
            '5f0c5ef8479b243d4d67e612': 'Santander Rio Personal Select',
            '5f2dc493fd79f92aec276c01': 'Banco Macro Empresas Nuevo',
            '5fcfcdc733a1e24d2d3e2612': 'Banco Municipal Empresas',
            '60e72485510da807ddd7c89a': 'Mercado Pago',
            '610c10f66b98cf59668dff59': 'Banco Bind Home Banking',
            '610c17422dae2f5aec631082': 'ICBC Multipay',

            # Chile
            '5910b923056f2905ea05bbc2': 'Banco de Chile Empresas',
            '5e349ca9ac8d7325fb717011': 'Banco de Chile Nuevo Portal',
            '60b7b896a6cb132835331fda': 'Santander Office Banking',
            '60dca020b591c74eebec61c4': 'BCI Empresas',

            # United States
            '5a29ccc0056f29062e404ec1': 'Coinbase',
            '5a85d00f056f290c504cf9f2': 'BTC Blockchain',
            '5a85d083056f290c4f19bdf2': 'ETH Blockchain',
            '5a85d146056f290c5117f1f2': 'Paypal Business',
            '5bdce2cf7d8b6b412a5c6902': 'Binance',
            '5bdce4737d8b6b3b0b347ca2': 'Bittrex',
            '5c0ec03cf9de2a0aab61d022': 'EOS Blockchain',

            # Uruguay
        }
        return data.get(id_site, 'Banco/Monedero no encontrado')

    def _fetch_transactions(self, refresh=True, accounts=False):
        self.ensure_one()
        if self.provider_type != 'paybook':
            return super()._fetch_transactions(refresh=refresh, accounts=accounts)

        bank_statement_line_ids = self.env['account.bank.statement.line']
        acc = accounts or self.account_online_account_ids
        for online_account in acc:
            # Only get transactions on account linked to a journal
            if online_account.journal_ids:
                bank_statement_line_ids += online_account._retrieve_transactions()

        # Actualizamos la info de la credencial, ya que si esta estaba con error tiene que marcarse como resuelta.
        self.action_paybook_update_state()

        self.show_result({
            'status': 'success',
            'message': _('Sincronizar transacciones'), 'added': len(bank_statement_line_ids)})
        return self._show_fetched_transactions_action(bank_statement_line_ids)
