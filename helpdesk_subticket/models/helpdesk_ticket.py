##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    parent_id = fields.Many2one(
        'helpdesk.ticket',
        string='Parent Ticket',
        index=True,
    )

    child_ids = fields.One2many(
        'helpdesk.ticket',
        'parent_id',
        string="Subtickets",
        copy=False,
    )

    subticket_count = fields.Integer(
        compute='_compute_subticket_count',
        type='integer',
        string="Subticket count",
    )

    def _compute_subticket_count(self):
        """ Compute subtickets """
        for ticket in self:
            ticket.subticket_count = self.search_count([('id', 'child_of', ticket.id), ('id', '!=', ticket.id)])

    def action_open_parent_ticket(self):
        """ Create parent ticket window action """
        return {
            'name': _('Parent Ticket'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'helpdesk.ticket',
            'res_id': self.parent_id.id,
            'type': 'ir.actions.act_window'
        }

    def action_subticket(self):
        ''' Create subticket window action '''
        action = self.env.ref(
            'helpdesk_subticket.helpdesk_ticket_action_subticket').sudo().read()[0]
        action['domain'] = [('id', 'child_of', self.id), ('id', '!=', self.id)]
        return action

    @api.constrains('parent_id')
    def _check_parent_id(self):
        ''' Validate that parent is not recursive '''
        for ticket in self:
            if not ticket._check_recursion():
                raise ValidationError(
                    _('Error: You cannot create recursive'
                      ' hierarchy of ticket(s).'))

    @api.constrains('stage_id')
    def _block_subtickets_unsolved(self):
        ''' Check if subtickets are done before closing parent '''
        if any(
            self.filtered(
                lambda t: t.stage_id.is_close
                and not all(t.child_ids.mapped('stage_id.is_close')))):
            raise ValidationError(
                _('Error: Before closing a parent ticket'
                   ' you should close the subticket(s).'))
