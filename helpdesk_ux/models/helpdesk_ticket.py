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

    def _track_template(self, changes):
        ticket = self[0]
        # PATCH START: Remove this part after odoo fix the error ...
        res = super()._track_template(changes)
        if 'stage_id' in changes and ticket.stage_id.template_id:
            res['stage_id'] = (ticket.stage_id.template_id, {
                'message_type': 'comment',
                'auto_delete_message': True,
                'email_layout_xmlid': 'mail.mail_notification_light'})
        # PATCH END: until this line
        if 'stage_id' in res and ticket.kanban_state == 'blocked' and \
                ticket.stage_id.template_id:
            res.pop('stage_id')
        return res
