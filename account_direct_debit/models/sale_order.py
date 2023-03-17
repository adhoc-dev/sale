from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _create_recurring_invoice(self, automatic=False, batch_size=30):
        """ Here is assigned to the invoice the direct debit mandate if the partner has one. This method is called if the invoice is created from scheduled action 'Sale Subscription: generate recurring invoices and payments' """
        account_moves = super()._create_recurring_invoice(automatic=automatic, batch_size=batch_size)
        for out_invoice_move in account_moves.filtered(lambda x: x.move_type == 'out_invoice' and x.partner_id):
            mandate = self.env['account.direct_debit.mandate'].search([
                ('partner_id.commercial_partner_id', '=', out_invoice_move.partner_id.commercial_partner_id.id),
                ('state', '=', 'active')], limit=1)
            out_invoice_move.direct_debit_mandate_id = mandate
        return account_moves
