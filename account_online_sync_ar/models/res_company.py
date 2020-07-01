from odoo import fields, models, api


class ResCompany(models.Model):

    _inherit = 'res.company'

    paybook_user_id = fields.Char("Paybook User ID")
    paybook_api_key = fields.Char("Paybook API KEY", groups="saas_client.group_saas_support")

    @api.model
    def setting_init_bank_account_action(self):
        """ overwrite completely to be able to create new journal when click Add a Bank Account instead of use the first
        bank journal defined """
        return self.env['account.journal'].action_choose_institution()
