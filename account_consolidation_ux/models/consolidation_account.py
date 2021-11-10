
from odoo import models, fields


class ConsolidationAccount(models.Model):
    _inherit = "consolidation.account"

    additional_domain = fields.Char(default='[]')
