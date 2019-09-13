##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################

from odoo import fields, models, api


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'
    _order = "priority desc, sequence, id"

    sequence = fields.Integer(
        index=True,
        default=10,
        help="Gives the sequence order when displaying a list of tickets."
    )

    @api.multi
    def _track_template(self, tracking):
        ticket = self[0]
        # PATCH START: Remove this part after odoo fix the error ...
        res = super()._track_template(tracking)
        changes, tracking_value_ids = tracking[ticket.id]
        if 'stage_id' in changes and ticket.stage_id.template_id:
            res['stage_id'] = (ticket.stage_id.template_id, {'auto_delete_message': True})
        # PATCH END: until this line

        # res = super(HelpdeskTicket, self)._track_template(tracking)
        if 'stage_id' in res and ticket.kanban_state == 'blocked' and \
                ticket.stage_id.template_id:
            res.pop('stage_id')
        return res
