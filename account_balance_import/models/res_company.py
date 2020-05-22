from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = "res.company"

    account_setup_ib_state = fields.Selection(
        [('not_done', "Not done"),
         ('done', "Done")],
        string="State of the onboarding Initial balance step",
        default='not_done',
    )

    @api.model
    def setting_intial_balances_action(self):
        """ Called by the 'Initial Balances' button of the setup bar."""
        form_view_id = self.env.ref(
            'account_balance_import.account_balance_import_wizard').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Initial Balances'),
            'view_mode': 'form',
            'res_model': 'account_balance_import',
            'target': 'new',
            'views': [[form_view_id, 'form']],
        }
