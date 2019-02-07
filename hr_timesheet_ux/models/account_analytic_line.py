##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import api, fields, models


class AccountAnalyticLine(models.Model):

    _inherit = 'account.analytic.line'

    @api.onchange('project_id')
    def onchange_project_id(self):
        """ Only filter by tasks that are active and not 100% progress yet.
        """
        res = super(AccountAnalyticLine, self).onchange_project_id()
        if isinstance(res, (dict,)) and res.get('domain', False):
            task_domain = res.get('domain').get('task_id', [])
            res['domain']['task_id'] = task_domain + [
                ('progress', '<', 100.0)]
        return res
