##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################

from odoo import models, fields


class PurchaseSubscriptionCloseReason(models.Model):
    _name = "purchase.subscription.close.reason"
    _order = "sequence, id"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
