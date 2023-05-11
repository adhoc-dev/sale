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

    invoicing_method = fields.Selection(
        selection=[('draft', 'Draft'),
            ('autopost', 'Autopost')],
        string='Invoice Method',
        default='autopost',
        required=True,
        help='This field can take the following values :\n'
             '  * Autopost: Invoices will be posted once they are created\n'
             '  * Draft: Invoices will not be posted and will stay in draft once they are created\n'
             'In any case, if there is a payment token, it will try to generate the payment and post the invoice',
    )

    add_period_dates_to_description = fields.Boolean(
        'Add Period Dates to Description',
        help='If setted, a description of the invoiced period will be added to the invoice narration',
        default=True,
    )
