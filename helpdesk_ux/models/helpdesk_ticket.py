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
        help="Gives the sequence order when "
        "displaying a list of tasks."
    )

    @api.multi
    def _track_template(self, tracking):
        res = super(HelpdeskTicket, self)._track_template(tracking)
        if self.kanban_state == 'blocked' and self.stage_id.template_id:
            'stage_id' in res and res.pop('stage_id')
        return res
