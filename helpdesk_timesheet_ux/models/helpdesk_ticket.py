##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HelpdeskTicket(models.Model):

    _inherit = 'helpdesk.ticket'


    project_id = fields.Many2one("project.project", related=False, readonly=False)

    @api.model_create_multi
    def create(self, list_value):
        """ On creating a ticket, if not user is set, then we get if from
        _onchange_team_id """
        recs = super().create(list_value)
        for rec in recs:
            if not rec.user_id and rec.team_id.assign_method == 'project_responsable':
                rec.user_id = rec.project_id.user_id
        return recs


    @api.depends('team_id')
    def _compute_user_and_stage_ids(self):
        super()._compute_user_and_stage_ids()
        for ticket in self.filtered(lambda ticket: ticket.team_id):
            if not ticket.user_id and ticket.team_id.assign_method == 'project_responsable':
                ticket.user_id = ticket.project_id.user_id
            elif ticket.user_id and ticket.team_id.assign_method == 'specific_user' and ticket.user_id != ticket.team_id.user_id:
                ticket.user_id = ticket.team_id.user_id
            elif ticket.user_id and ticket.team_id.assign_method == 'unassigned':
                ticket.user_id = self.env['res.users']


    @api.onchange('project_id')
    def _onchange_project(self):
        """ Bring default partner_id if ticket created from project """
        if not self.partner_id and self.project_id and self.project_id.partner_id:
            self.partner_id = self.project_id.partner_id
