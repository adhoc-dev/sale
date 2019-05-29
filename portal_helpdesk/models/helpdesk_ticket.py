##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models


class HelpdeskTicket(models.Model):

    _inherit = 'helpdesk.ticket'

    user_id = fields.Many2one(
        domain=[],
    )
