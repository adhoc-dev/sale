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

    dont_send_stage_email = fields.Boolean(
        string="Don't Send Stage Email",
        default=False,
        help="When the ticket's stage changes, if the stage has an automatic template set, "
        "no email will be send. After the stage changes, this value returns to False so that "
        "new stage changes will send emails."
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
        if 'stage_id' in res and ticket.dont_send_stage_email == True and\
            ticket.stage_id.template_id:
            res.pop('stage_id')
            ticket.dont_send_stage_email = False
        return res
