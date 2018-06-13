##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    purchase_subscription_id = fields.Many2one('purchase.subscription')
