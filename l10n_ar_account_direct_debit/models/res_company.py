from odoo import fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    galicia_creditor_identifier = fields.Char(string='Número de prestación débito automático Galicia', help='Galicia Automatic Debit identifier of the company, given by the bank.')
    direct_debit_merchant_number = fields.Char(string='Número de comercio (tarjeta de crédito Master)')
