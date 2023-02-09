from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_invoice_subscription(self):
        """ Here is assigned to the invoice the direct debit mandate if the partner has one """
        res = super().action_invoice_subscription()

        if res.get('res_id'):
            account_move = self.env['account.move'].browse(res.get('res_id'))
        else:
            account_move = self.env['account.move'].search(res.get('domain'))

        moves = account_move.filtered(lambda x: x.move_type == 'out_invoice' and x.partner_id)
        for out_invoice_move in moves:
            mandate = self.env['account.direct_debit.mandate'].search([
                ('partner_id.commercial_partner_id', '=', out_invoice_move.partner_id.commercial_partner_id.id),
                ('state', '=', 'active')], limit=1)
            out_invoice_move.direct_debit_mandate_id = mandate
        return res
