# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.payment'

    direct_debit_mandate_id = fields.Many2one(
        'account.direct_debit.mandate',
        # TODO mas adelante se podria convertir en readonly = False y permitir generar
        readonly=True, states={'draft': [('readonly', False)]}, ondelete='restrict',
    )
