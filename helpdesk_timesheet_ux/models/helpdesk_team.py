##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class HelpdeskTeam(models.Model):

    _inherit = 'helpdesk.team'

    assign_method = fields.Selection(
        selection_add=[
            ("project_responsable", "Project Responsable"),
            ("specific_user", "Specific User"),
            ("unassigned", "Unassigned"),
        ],
        ondelete={'project_responsable': 'set default', 'specific_user': 'set default', 'unassigned': 'set default'},
    )

    user_id = fields.Many2one(
        'res.users',
        'Specific user',
        domain=lambda self: [
            ('groups_id', 'in', self.env.ref(
                'helpdesk.group_helpdesk_user').id)],
    )

    @api.constrains('assign_method', 'member_ids')
    def _check_member_assignation(self):
        if not self.member_ids and self.assign_method in [
                'randomly', 'balanced']:
            raise ValidationError(_(
                "You must have team members assigned to change the "
                "assignation method."))

    def write(self, vals):
        """ If use_helpdesk_timesheet then set the related project to
        allow_tickets
        """
        if 'use_helpdesk_timesheet' in vals:
            projects = self.filtered('use_helpdesk_timesheet').mapped('project_id')
            if projects:
                projects.write({'allow_tickets': True})
        return super().write(vals)

    @api.model
    def create(self, vals):
        """ If use_helpdesk_timesheet then set the related project to
        allow_tickets
        """
        res = super().create(vals)
        if res.use_helpdesk_timesheet and res.project_id:
            res.project_id.allow_tickets = True
        return res

    def _determine_user_to_assign(self):
        """ We add for 2 cases of assination of user from the team.
        """
        result = super()._determine_user_to_assign()
        for team in self:
            if team.assign_method == 'unassigned':
                result[team.id] = self.env['res.users']
            elif team.assign_method == 'specific_user':
                result[team.id] = team.user_id
        return result
