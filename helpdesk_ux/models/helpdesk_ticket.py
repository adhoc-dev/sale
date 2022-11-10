##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################

from odoo import fields, models


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
        res = super()._track_template(changes)
        if 'stage_id' in res and ticket.dont_send_stage_email == True and\
            ticket.stage_id.template_id:
            res.pop('stage_id')
            ticket.dont_send_stage_email = False
        return res

    def search(self, domain, offset=0, limit=None, order=None, count=False):
        if self._context.get('order_by_priority'):
            order = 'stage_id, {}'.format(self._order)
        return super().search(domain=domain, offset=offset, limit=limit, order=order, count=count)
