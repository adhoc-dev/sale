##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields


class SaleSubscriptionTemplate(models.Model):

    _inherit = "sale.subscription.template"

    dates_required = fields.Boolean(
        "Dates Required",
    )

    period = fields.Integer(
        string='Period',
        help='If you set a period, then when changing date "Start Date" '
        'the "End Date" will be automatically updated'
    )

    copy_description_to_invoice = fields.Boolean(
        help="Copy Subscription Template description to recurring invoices")
