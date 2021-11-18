##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    def _prepare_subscription_data(self, template):
        res = super()._prepare_subscription_data(template)
        if template.use_different_invoice_address and self.partner_invoice_id != self.partner_id:
            res.update({'partner_invoice_id': self.partner_invoice_id.id})
        return res
