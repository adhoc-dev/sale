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
        return self.env['account.online.provider'].with_context(journal_id=self.journal_id.id)._paybook_open_login()

    def action_open_saltedge(self):
        self.check_terms_and_conditions()
        return safe_eval(self.default_action)

    def action_open_wiz(self):
        return {
            'name': _('Seleccione Proveedor de Sincronización Bancaria'),
            'target': 'new',
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'type': 'ir.actions.act_window',
        }
