from odoo import models, fields

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    task_id = fields.Many2one(domain="[('project_id.allow_timesheets', '=', True), ('project_id', '=?', project_id)]")
