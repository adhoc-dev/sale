# -*- coding: utf-8 -*-
from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    direct_debit_mandate_id = fields.Many2one(
        'account.direct_debit.mandate',
        compute='_compute_direct_debit_mandate',
        store=True,
        readonly=False,
        ondelete='restrict',
        help='If configured, when posting the invoice a payment will be automatically created using '
        'this mandate')

    @api.depends('partner_id')
    def _compute_direct_debit_mandate(self):
        for rec in self.filtered(lambda x: x.type == 'out_invoice'):
            mandate = False
            if rec.partner_id:
                mandate = self.env['account.direct_debit.mandate'].search([
                    ('partner_id.commercial_partner_id', '=', rec.partner_id.commercial_partner_id.id),
                    ('state', '=', 'active')], limit=1)
            rec.direct_debit_mandate_id = mandate

    def action_post(self):
        res = super().action_post()
        self.direct_debit_payment()
        return res

    def direct_debit_payment(self):
        # validate_payment = not self._context.get('validate_payment')
        for rec in self.filtered(
                lambda x: x.direct_debit_mandate_id and x.state == 'posted' and
                x.invoice_payment_state == 'not_paid' and x.type == 'out_invoice'):
            # TODO remove on v15 key create_from_expense, needed on v13 for payment group to be created
            # This code is only executed if the mandate may be used (thanks to the previous UserError)
            payment = self.env['account.payment'].with_context(
                active_id=rec.id, active_ids=rec.ids, create_from_expense=True).create({
                    'invoice_ids': [(4, rec.id, None)],
                    'journal_id': rec.direct_debit_mandate_id.journal_id.id,
                    'payment_method_id': rec.env.ref('account_direct_debit.payment_method_direct_debit').id,
                    'direct_debit_mandate_id': rec.direct_debit_mandate_id.id,
                    'amount': rec.amount_residual,
                    'currency_id': rec.currency_id.id,
                    'payment_type': 'inbound',
                    'communication': rec.ref or rec.name,
                    'partner_type': 'customer' if rec.type == 'out_invoice' else 'supplier',
                    'partner_id': rec.partner_id.commercial_partner_id.id,
                    'payment_date': rec.invoice_date_due or rec.invoice_date
                })
            payment.post()
