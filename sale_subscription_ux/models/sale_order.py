##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, api


class SaleOrder(models.Model):

    _inherit = "sale.order"

    @api.constrains('analytic_account_id')
    def set_analytic_account(self):
        """  First the subscriptions are created and then the Project and
        Tasks related to the sale order.

        We want to ensure that after the account_analytic_id from sale order
        is generated (via product service tracking) we are able to set the
        same analytic_account_id to the already created subscriptions.
        """
        for sale in self:
            analytic_account = sale.analytic_account_id
            subscriptions = \
                sale.order_line.mapped('subscription_id').filtered(
                    lambda x: not x.analytic_account_id)
            if not analytic_account or not subscriptions:
                continue

            subscriptions.write({
                'analytic_account_id': analytic_account.id})
