##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
import logging
from odoo import models, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.addons.google_account.models.google_service import GOOGLE_TOKEN_ENDPOINT
from odoo.addons.website_doc.google_docs_tools import read_structural_elements
from odoo.exceptions import UserError, RedirectWarning

from werkzeug.urls import url_encode, url_join
import requests
import time


# google apis
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

_logger = logging.getLogger(__name__)


class googleService(models.AbstractModel):

    _inherit = 'google.service'

    @api.model
    def _gs_auth2_set_token(self, creds):
        param_sudo = self.env['ir.config_parameter'].sudo()
        token = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "expiry": creds.expiry.isoformat(sep='T')
        }
        param_sudo.set_param('gs_auth2.token_json', token)

    @api.model
    def _gs_auth2_get_token(self):
        try:
            param_sudo = self.env['ir.config_parameter'].sudo()
            token = safe_eval(param_sudo.get_param('gs_auth2.token_json'))
            token.update({"client_secret": param_sudo.get_param('gs_auth2.client_secret')})
            return token
        except ValueError:
            url = self.get_consent_uri()
            action = {
                'name': 'Activar credencial',
                'res_model': 'ir.actions.act_url',
                'type': 'ir.actions.act_url',
                'target': '_blank',
                'url': url
               }

            raise RedirectWarning(_('No hay una credencial de acceso a google.'), action, _('Activar credencial'))

    def gs_auth2_cred(self):
        token = self._gs_auth2_get_token()
        creds = Credentials.from_authorized_user_info(token, self._SERVICE_SCOPE)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            self._gs_auth2_set_token(creds)
        return creds

    @api.model
    def copy_document(self, orig_document_id, doc_title):
        creds = self.gs_auth2_cred()
        service = build('drive', 'v3', credentials=creds)
        body = {
            'name': doc_title,
            'supportsAllDrives': True,
        }
        drive_response = service.files().copy(
            fileId=orig_document_id, body=body
        ).execute()
        return drive_response.get('id')

    @api.model
    def read_document(self, document_id):
        creds = self.gs_auth2_cred()
        doc_content = self._get_document(creds, document_id)
        return read_structural_elements(doc_content)

    @api.model
    def _get_document(self, creds, document_id):
        service = build('docs', 'v1', credentials=creds)
        doc = service.documents().get(documentId=document_id).execute()
        return doc.get('body').get('content')

    @api.model
    def credentials_user_info(self):
        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = self._gs_auth2_get_token()

        _dummy, response, _dummy = self.env['google.service']._do_request(
            GOOGLE_TOKEN_ENDPOINT,
            params=data,
            headers=headers,
            method='POST',
            preuri=''
        )
        self._gs_auth2_set_token(response)
        return response

    def get_consent_uri(self):
        param_sudo = self.env['ir.config_parameter'].sudo()
        client_id = param_sudo.get_param('gs_auth2.client_id')
        base_url = self.get_base_url()
        redirect_uri = url_join(base_url, '/website_doc/confirm')

        return 'https://accounts.google.com/o/oauth2/v2/auth?%s' % url_encode({
                    'client_id': client_id,
                    'redirect_uri': redirect_uri,
                    'response_type': 'code',
                    'scope': ' '.join(self._SERVICE_SCOPE),
                    # access_type and prompt needed to get a refresh token
                    'access_type': 'offline',
                    'prompt': 'consent',
                })

    def _fetch_refresh_token(self, authorization_code):
        """Request the refresh token and the initial access token from the authorization code.

        :return:
            refresh_token, access_token, access_token_expiration
        """
        response = self._fetch_token('authorization_code', code=authorization_code)

        return (
            response['refresh_token'],
            response['access_token'],
            int(time.time()) + response['expires_in'],
        )

    def _fetch_token(self, grant_type, **values):
        """Generic method to request an access token or a refresh token.

        :param grant_type: Depends the action we want to do (refresh_token or authorization_code)
        :param values: Additional parameters that will be given to the GMail endpoint
        """
        param_sudo = self.env['ir.config_parameter'].sudo()
        client_id = param_sudo.get_param('gs_auth2.client_id')
        client_secret = param_sudo.get_param('gs_auth2.client_secret')
        base_url = self.get_base_url()
        redirect_uri = url_join(base_url, '/website_doc/confirm')

        response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': grant_type,
                'redirect_uri': redirect_uri,
                **values,
            },
            timeout=5,
        )
        _logger.info(response.text)
        if not response.ok:
            raise UserError(_('An error occurred when fetching the access token.'))

        return response.json()