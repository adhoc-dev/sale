# -*- coding: utf-8 -*-
from odoo import fields, models, _


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    # TODO borrar o agregar campos necesarios
    direct_debit_format = fields.Selection(selection_add=[
        ('cbu_macro', 'CBU Macro'),
        ('cbu_galicia', 'CBU Galicia'),
        ('visa_credito', 'VISA Crédito'),
        ('master_credito', 'Master Crédito'),
        ('visa_debito', 'VISA Débito'),
    ])
