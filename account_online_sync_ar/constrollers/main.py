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

    @route(['/account_online_sync_ar/paybook_success/'],  methods=['POST'], type='http', auth='user', csrf=False)
    def success_paybook(self, **post):
        if post:
            return request.env['account.online.provider']._paybook_success(post)
