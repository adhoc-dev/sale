from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ResCompany(models.Model):

    _inherit = 'res.company'

    paybook_user_id = fields.Char("Paybook User ID")

    @api.model
    def setting_init_bank_account_action(self):
        """ overwrite completely to be able to create new journal when click Add a Bank Account instead of use the first
        bank journal defined """
        default_action = self.env['account.journal'].action_configure_bank_journal()
        provider_link = self.env['provider.link'].create({
            # 'journal_id': self.id,
            'default_action': default_action})
        return provider_link.action_open_wiz()

    def _paybook_get_user_token(self, id_user=False):
        raise UserError(_('Falta configuración de credenciales de ADHOC para consulta del user token'))

    def _paybook_register_new_user(self):
        raise UserError(_('Falta configuración de credenciales de ADHOC para creacion de new user'))
