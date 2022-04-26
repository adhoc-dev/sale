from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError


class ProviderLink(models.TransientModel):

    _name = 'provider.link'
    _description = 'Provider Link'

    journal_id = fields.Many2one('account.journal')
    details = fields.Html()
    default_action = fields.Text()
    ok_terms = fields.Boolean("Acepto Términos y Condiciones")

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res['details'] = """Por favor lea la siguiente <a href="https://www.adhoc.com.ar/doc/2853/6839">documentación</a> antes de comenzar"""
        return res

    def check_terms_and_conditions(self):
        if not self.ok_terms:
            raise UserError(_('No puede continuar hasta tanto no acepte los términos y condiciones del servicio'))

    def action_open_paybook(self):
        self.check_terms_and_conditions()
        return self.env['account.online.link'].with_context(journal_id=self.journal_id.id)._paybook_open_login()

    def action_open_saltedge(self):
        self.check_terms_and_conditions()
        return safe_eval(self.default_action)

    def action_open_wiz(self):
        view_id = self.env.ref('account_online_sync_ar.provider_link_view_form').id
        return {
            'name': _('Seleccione Proveedor de Sincronización Bancaria'),
            'target': 'new',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [[view_id, 'form']],
            'res_model': self._name,
            'type': 'ir.actions.act_window',
        }

    def action_open_manual(self):
        """ let the user to create the bank without any sincronization"""
        view_id = self.env.ref('account.setup_bank_account_wizard').id
        ctx = self.env.context.copy()
        if self.env.context.get('active_model') == 'account.journal':
            ctx.update({
                'default_linked_journal_id': ctx.get('journal_id', False)
            })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create a Bank Account'),
            'res_model': 'account.setup.bank.manual.config',
            'target': 'new',
            'view_mode': 'form',
            'views': [[view_id, 'form']],
            'context': ctx,
        }
