##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields


class SaleSubscriptionTemplate(models.Model):

    _inherit = "sale.subscription.template"

    use_different_invoice_address = fields.Boolean(
        string="Use different invoice address?",
        help="Set specific billing partner (that could be different from subscription partner)",
    )
    dates_required = fields.Boolean(
        "Dates Required",
    )
    copy_description_to_invoice = fields.Boolean(
        help="Copy Subscription Template description to recurring invoices")
    do_not_update_price = fields.Boolean(
        help="Don't update price when quantity change"
    )
    add_period_dates_to_description = fields.Boolean(
        'Add Period Dates to Description',
        help='If setted, a description of the invoiced period will be added to the invoice narration',
        default=True,
    )
