from odoo.http import Controller, request, route


class PaybookPortal(Controller):

    @route(['/account_online_sync_ar/configure_paybook/<int:company_id>/<int:journal_id>/'], type='http', auth='user',
           website=True)
    def configure_paybook(self, company_id, journal_id, redirect=None, **post):
        company = request.env['res.company'].sudo().browse(company_id)
        values = {
            'company_id': company_id,
            'journal_id': journal_id,
            'paybook_user_token': company._paybook_get_user_token()}
        response = request.render("account_online_sync_ar.paybook_login", values)
        return response

    @route(['/account_online_sync_ar/update_bank/<int:company_id>/<int:journal_id>/<int:online_link_id>'], type='http', auth='user',
           website=True)
    def update_bank(self, company_id, journal_id, online_link_id, redirect=None, **post):
        company = request.env['res.company'].sudo().browse(company_id)
        online_link = request.env['account.online.link'].sudo().browse(online_link_id)
        values = {
            'company_id': company_id,
            'journal_id': journal_id,
            'paybook_user_token': company._paybook_get_user_token(),
            'id_credential': online_link.client_id,
            'id_site': online_link.provider_identifier,
        }
        # TODO KZ scripts provider_account_identifier (account.online.provider)  ahora es client_id (account_online_link)
        response = request.render("account_online_sync_ar.update_credential", values)
        return response

    @route(['/account_online_sync_ar/paybook_success/'], methods=['POST'], type='http', auth='user', csrf=False)
    def success_paybook(self, **post):
        if post:
            return request.env['account.online.link']._paybook_success(post)

    @route(['/account_online_sync_ar/update_success/'],  methods=['POST'], type='http', auth='user', csrf=False)
    def update_success(self, **post):
        if post:
            return request.env['account.online.link']._update_cred_response(post)
