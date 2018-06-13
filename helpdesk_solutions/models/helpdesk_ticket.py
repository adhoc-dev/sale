##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, api, _
from odoo.tools import html2plaintext
from odoo.exceptions import ValidationError


class HelpdeskTicket(models.Model):

    _inherit = 'helpdesk.ticket'

    helpdesk_solution_id = fields.Many2one(
        'helpdesk.solution',
        string='Linked Solution',
    )
    ticket_description = fields.Html(
    )
    solution_description = fields.Html(
    )

    @api.constrains('stage_id')
    def change_stage_id(self):
        for rec in self.filtered("stage_id.solution_required"):
            if len(html2plaintext(rec.solution_description)) <= 1:
                raise ValidationError(_(
                    'You need to complete solution'
                    ' description to change the stage'))
