##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, api


class HelpdeskSolution(models.Model):

    _inherit = 'helpdesk.solution'

    task_ids = fields.One2many(
        'project.task',
        'helpdesk_solution_id',
        string='Tasks',
    )
    task_count = fields.Integer(
        compute='_compute_task_count',
        store=True,
    )

    @api.depends('task_ids')
    def _compute_task_count(self):
        """ Amount of tasks related to this Helpdesk Solution
        """
        for rec in self:
            rec.task_count = len(rec.task_ids)
