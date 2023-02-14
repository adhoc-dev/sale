from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    direct_debit_mandate_id = fields.Many2one(
        'account.direct_debit.mandate',
        store=True,
        readonly=False,
        ondelete='restrict',
        help='If configured, when posting the invoice a payment will be automatically created using '
        'this mandate')


    def _post(self, soft=True):
        res = super()._post(soft=soft)
        to_pay_moves = self.filtered(
                lambda x: x.direct_debit_mandate_id.journal_id and x.state == 'posted' and
                x.payment_state == 'not_paid' and x.move_type == 'out_invoice')
        to_pay_moves.direct_debit_payment()
        return res

    def direct_debit_payment(self):
        for rec in self:
            # This code is only executed if the mandate may be used (thanks to the previous UserError)
            # clean active_ids and active_id on context because when posting multiple invoices at once
            # this method is called one by one but active_ids has all the invoices and then default_get of payment will
            # raise an error that not every invoice is posted
            payment = self.env['account.payment'].with_context(
                active_ids=False, active_id=rec.id).create({
                    'journal_id': rec.direct_debit_mandate_id.journal_id.id,
                    'payment_method_line_id':
                        rec.direct_debit_mandate_id.journal_id._get_available_payment_method_lines('inbound').filtered(
                            lambda x: x.code == 'dd').id,
                    'direct_debit_mandate_id': rec.direct_debit_mandate_id.id,
                    'amount': rec.amount_residual,
                    'currency_id': rec.currency_id.id,
                    'payment_type': 'inbound',
                    # TODO evaluar si no debería tomar primero payment_ref? que hace odoo en otros lugares
                    'ref': rec.ref or rec.name,
                    'partner_type': 'customer' if rec.move_type == 'out_invoice' else 'supplier',
                    'partner_id': rec.partner_id.commercial_partner_id.id,
                    'date': rec.invoice_date_due or rec.invoice_date,
                    'asset_remaining_value': 0.0,
                    'asset_depreciated_value': 0.0,
                })
            payment.action_post()
            (rec.line_ids + payment.line_ids).filtered_domain([
                ('parent_state', '=', 'posted'),
                ('account_type', 'in', ('asset_receivable', 'liability_payable')),
                ('reconciled', '=', False),
            ]).reconcile()
