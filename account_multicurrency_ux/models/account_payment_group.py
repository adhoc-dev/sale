from odoo import models, fields


class AccountPaymentGroup(models.Model):

    _inherit = "account.payment.group"

    exchange_diff_adjustment_required = fields.Boolean(
        readonly=True,
        string='Requiere ajuste por diferencia de cambio',
        compute='_compute_exchange_diff_adjustment_required',
    )

    def _compute_exchange_diff_adjustment_required(self):
        for rec in self:
            rec.exchange_diff_adjustment_required = any(
                x.exchange_diff_adjustment_required for x in rec.move_line_ids.mapped('matched_debit_ids'))
