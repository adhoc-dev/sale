##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    allow_tickets = fields.Boolean("Allow tickets", default=False)

    @api.constrains('active')
    def validate_active_from_tickets(self):
        for project in self.filtered(lambda x: not x.active and x.ticket_ids):
            open_tickets = project.ticket_ids.filtered(
                lambda x: not x.stage_id.fold)
            if open_tickets:
                raise ValidationError(
                    _("You can not close a project with active tickets,"
                      " we consider active ticket the one in stages "
                      "without option 'folded' (ticket IDs %s)" %
                      open_tickets.ids))

    @api.depends('ticket_ids.project_id')
    def _compute_ticket_count(self):
        if not self.user_has_groups('helpdesk.group_helpdesk_user'):
            self.ticket_count = 0
            return
        result = self.env['helpdesk.ticket'].read_group([
            ('project_id', 'in', self.ids), ('stage_id.fold', '=', False)
        ], ['project_id'], ['project_id'])
        data = {data['project_id'][0]: data['project_id_count']
                for data in result}
        for project in self:
            project.ticket_count = data.get(project.id, 0)

    def action_open_project_tickets(self):
        action = super().action_open_project_tickets()
        action.update({
            'context': {'active_id': self.id, 'default_project_id': self.id},
        })
        return action
