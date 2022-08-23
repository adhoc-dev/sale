##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, api, _
from odoo.tools import html2plaintext
from odoo.exceptions import ValidationError


class Task(models.Model):

    _inherit = 'project.task'

    helpdesk_solution_id = fields.Many2one(
        'helpdesk.solution',
        string='Linked Solution',
    )
    task_description = fields.Html()
    solution_description = fields.Html()

    @api.constrains('stage_id')
    def change_stage_id(self):
        recs = self.filtered(lambda x: (
                x.partner_id and
                x.stage_id.solution_required and
                len(html2plaintext(x.solution_description)) <= 1 and
                len(html2plaintext(x.helpdesk_solution_id.customer_solution_description or '')) <= 1))
        if recs:
            raise ValidationError(_(
                'You need to complete solution description to change the stage. Rec ids: %s') % recs.ids)

    def copy_solution(self):
        for rec in self:
            rec.solution_description = rec.helpdesk_solution_id.customer_solution_description
