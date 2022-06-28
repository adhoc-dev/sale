from odoo import fields, models, _


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    direct_debit_format = fields.Selection([])
