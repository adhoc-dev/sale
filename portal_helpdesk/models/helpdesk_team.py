##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models


class HelpdeskTeam(models.Model):

    _inherit = 'helpdesk.team'

    user_id = fields.Many2one(
        domain=[],
    )

    member_ids = fields.Many2many(
        domain=[],
    )
