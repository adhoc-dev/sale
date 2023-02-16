##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models


class ProjectTaskType(models.Model):

    _inherit = 'project.task.type'

    solution_required = fields.Boolean(
        string="Solution Required?",
        help='If you set it to true, then tasks that has a contact and are'
        'moved to this stage will require a solution.'
    )