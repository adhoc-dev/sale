from odoo import models, fields


class AccountBatchPayment(models.Model):
    _inherit = 'account.batch.payment'

    direct_debit_collection_date = fields.Date(
        string='Collection date', default=fields.Date.today, readonly=True,
        states={'draft': [('readonly', False)]},
        help="Date when the company expects to receive the payments of this batch.")
    direct_debit_format = fields.Selection(related='journal_id.direct_debit_format')
