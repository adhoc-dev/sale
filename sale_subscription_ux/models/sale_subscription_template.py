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
    copy_description_to_invoice = fields.Boolean(
        help="Copy Subscription Template description to recurring invoices")
    do_not_update_price = fields.Boolean(
        help="Don't update price when quantity change"
    )
