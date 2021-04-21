##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, api


class HelpdeskSolution(models.Model):

    _name = 'helpdesk.solution'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Helpdesk Solution"
    _order = 'ticket_count desc'

    name = fields.Char(
        required=True,
    )
    internal_solution_description = fields.Html(
    )
    customer_solution_description = fields.Html(
    )
    ticket_description = fields.Html(
    )
    tag_ids = fields.Many2many(
        'helpdesk.solution.tag',
        string='Tags',
    )
    faq_category_ids = fields.Many2many(
        'helpdesk.solution.faq.category',
        string='FAQ Categories',
    )
    ticket_ids = fields.One2many(
        'helpdesk.ticket',
        'helpdesk_solution_id',
        string='Tickets',
    )
    ticket_count = fields.Integer(
        compute='_compute_ticket_count',
        store=True,
    )
    active = fields.Boolean(
        default=True,
        copy=False,
    )

    @api.depends('ticket_ids')
    def _compute_ticket_count(self):
        """ Amount of tickets related to this Helpdesk Solution
        """
        for rec in self:
            rec.ticket_count = len(rec.ticket_ids)
