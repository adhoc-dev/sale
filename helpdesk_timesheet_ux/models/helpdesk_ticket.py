##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, api, _
from odoo.exceptions import ValidationError


class HelpdeskTicket(models.Model):

    _inherit = 'helpdesk.ticket'

    @api.model
    def create(self, vals):
        """ On creating a ticket, if not user is set, then we get if from
        _onchange_team_id """
        rec = super().create(vals)
        if not rec.user_id and rec.team_id.assign_method == 'project_responsable':
            rec.user_id = rec.project_id.user_id
        return rec



    @api.depends('team_id')
    def _compute_user_and_stage_ids(self):
        super()._compute_user_and_stage_ids()
        for ticket in self.filtered(lambda ticket: ticket.team_id):
            if not ticket.user_id and ticket.team_id.assign_method == 'project_responsable':
                ticket.user_id = ticket.project_id.user_id

    @api.onchange('project_id')
    def _onchange_project(self):
        """ Bring default partner_id if ticket created from project """
        if not self.partner_id and self.project_id and self.project_id.partner_id:
            self.partner_id = self.project_id.partner_id
