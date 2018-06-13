##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models


class HelpdeskStage(models.Model):

    _inherit = 'helpdesk.stage'

    solution_required = fields.Boolean(
        string="Solution Required?",
        help='If you set it to true, then tickets that moves into this stage '
        'will require a solution.'
    )
