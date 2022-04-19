# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    galicia_creditor_identifier = fields.Char(related='company_id.galicia_creditor_identifier', readonly=False)
    direct_debit_merchant_number = fields.Char(related='company_id.direct_debit_merchant_number', readonly=False)
