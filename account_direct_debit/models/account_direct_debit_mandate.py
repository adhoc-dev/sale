from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SDDMandate(models.Model):
    """ A class containing the data of a mandate sent by a customer to give its
    consent to a company to collect the payments associated to his invoices
    using BANK Direct Debit.
    """
    _name = 'account.direct_debit.mandate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Direct Debit Mandates'
    _check_company_auto = True
    _rec_name = 'journal_id'

    state = fields.Selection(
        [('draft', 'Draft'), ('active', 'Active'), ('closed', 'Closed')],
        string="State",
        readonly=True,
        tracking=True,
        default='draft',
        help="The state this mandate is in. \n"
        "- 'draft' means that this mandate still needs to be confirmed before being usable. \n"
        "- 'active' means that this mandate can be used to pay invoices. \n"
        "- 'closed' designates a mandate that has been marked as not to be uses anymore.")
    description = fields.Char()
    partner_id = fields.Many2one(
        'res.partner', string='Customer', required=True, readonly=True, states={'draft': [('readonly', False)]},
        help="Customer whose payments are to be managed by this mandate.")
    commercial_partner_id = fields.Many2one(related='partner_id.commercial_partner_id', store=True)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company,
        help="Company for whose invoices the mandate can be used.")
    paid_invoice_ids = fields.One2many(
        'account.move', 'direct_debit_mandate_id', string='Invoices Paid', readonly=True,
        help="Invoices paid using this mandate.")
    journal_id = fields.Many2one(
        'account.journal', string='Journal', check_company=True,
        readonly=True, states={'draft': [('readonly', False)]},
        help='Journal to use to receive Direct Debit payments from this mandate.')
    direct_debit_format = fields.Selection(related='journal_id.direct_debit_format')
    paid_invoices_nber = fields.Integer(
        string='# Paid Invoices', compute='_compute_paid_invoices_nber', help="Number of invoices paid with thid mandate.")

    @api.ondelete(at_uninstall=True)
    def unlink_direct_debit_mandate(self):
        if self.filtered(lambda x: x.state != 'draft'):
            raise UserError(_("Only mandates in draft state can be deleted from database when cancelled."))

    @api.depends('paid_invoice_ids')
    def _compute_paid_invoices_nber(self):
        for record in self:
            record.paid_invoices_nber = len(record.paid_invoice_ids)

    def action_validate_mandate(self):
        self.write({'state': 'active'})

    def action_to_draft(self):
        self.write({'state': 'draft'})

    def action_close_mandate(self):
        self.write({'state': 'closed'})

    def action_view_paid_invoices(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Paid Invoices'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.mapped('paid_invoice_ids').ids)],
        }
