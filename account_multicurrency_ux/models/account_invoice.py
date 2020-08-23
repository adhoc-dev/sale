from odoo import models, api, fields


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    exchange_diff_adjustment_required = fields.Boolean(
        readonly=True,
        string='Requiere ajuste por diferencia de cambio',
        compute='_compute_exchange_diff_adjustment_required',
        search='_search_exchange_diff_adjustment_required',
    )
    exchange_diff_ignored = fields.Boolean(
        track_visibility='onchange',
        string='Ajuste por diferencia de cambio ignorado',
        inverse='_inverse_exchange_diff_ignored',
        compute='_compute_exchange_diff',
        search='_search_exchange_diff_ignored',
    )
    exchange_diff_invoice_ids = fields.Many2many(
        'account.invoice',
        compute='_compute_exchange_diff',
        string='NC/ND de ajuste por dif de cambio',
    )

    def open_partial_reconciles(self):
        self.ensure_one()
        actions = self.env.ref('account_ux.action_account_move_partial_reconcile')
        action_read = actions.read()[0]
        action_read['domain'] = [('id', 'in', self.move_id.line_ids.mapped('matched_credit_ids').ids)]
        return action_read

    @api.multi
    def unignore_exchange_diff(self):
        self.write({'exchange_diff_ignored': False})

    def _inverse_exchange_diff_ignored(self):
        for rec in self:
            rec.move_id.line_ids.mapped('matched_credit_ids').write({'exchange_diff_ignored': rec.exchange_diff_ignored})

    def _compute_exchange_diff(self):
        for rec in self:
            rec.exchange_diff_invoice_ids = rec.move_id.line_ids.mapped('matched_credit_ids.exchange_diff_invoice_id')
            rec.exchange_diff_ignored = any(x.exchange_diff_ignored for x in rec.move_id.line_ids.mapped('matched_credit_ids'))

    def _compute_exchange_diff_adjustment_required(self):
        for rec in self:
            rec.exchange_diff_adjustment_required = any(
                x.exchange_diff_adjustment_required for x in rec.move_id.line_ids.mapped('matched_credit_ids'))

    def _search_exchange_diff_adjustment_required(self, operator, value):
        return [('move_id.line_ids.matched_credit_ids.exchange_diff_adjustment_required', operator, value)]

    def _search_exchange_diff_ignored(self, operator, value):
        return [('move_id.line_ids.matched_credit_ids.exchange_diff_ignored', operator, value)]
