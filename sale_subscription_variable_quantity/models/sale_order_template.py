##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields


class SaleOrderTemplate(models.Model):

    _inherit = "sale.order.template"

    dates_required = fields.Boolean(
        "Dates Required",
    )

    add_period_dates_to_description = fields.Boolean(
        'Add Period Dates to Description',
        help='If setted, a description of the invoiced period will be added to the invoice narration',
        default=True,
    )
