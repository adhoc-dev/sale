from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        #For Adhoc Migration - Task pending to add selection feature
        if self._context.get('disable_action_post'):
            return
        return super().action_post()
