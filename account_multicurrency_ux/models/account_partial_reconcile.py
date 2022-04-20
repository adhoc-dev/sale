from odoo import models, api, fields, _
from odoo.exceptions import UserError


class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"

    exchange_diff_adjustment_required = fields.Boolean(
        readonly=True,
        string='Requiere ajuste por diferencia de cambio',
        compute='_compute_exchange_diff_adjustment_required',
        store=True,
    )
    exchange_diff_ignored = fields.Boolean(
    )
    exchange_diff_invoice_id = fields.Many2one(
        'account.move',
        string='NC/ND de ajuste por dif de cambio',
    )

    @api.onchange('exchange_diff_ignored', 'exchange_diff_invoice_id')
    def _change_exchange_diff(self):
        return {'warning': {
            'title': _("Warning"),
            'message': _(
                'Cuidado si cambia informacion referente a los ajustes de cambio, según el caso podrá ser '
                'necesario que anule alguna NC/ND con otra NC/ND.')}}

    def _get_partial_adjustment_vals(self):
        partial_vals = {}
        for rec in self.filtered(
                lambda x: x.amount and x.debit_move_id.currency_id and x.debit_move_id.amount_currency and
                x.debit_move_id.move_id.move_type == 'out_invoice' and not x.exchange_diff_ignored and x.exchange_diff_invoice_id.state not in ['posted']):
            debit_line = rec.debit_move_id
            credit_line = rec.credit_move_id
            # TODO as we only allow invoices perhas we can use invoice rate directly
            invoice_rate = debit_line.balance / debit_line.amount_currency
            if credit_line.currency_id and credit_line.currency_id == debit_line.currency_id and credit_line.amount_currency:
                credit_rate = credit_line.balance / credit_line.amount_currency
            else:
                credit_rate = debit_line.currency_id._convert(
                    1.0, rec.company_id.currency_id, rec.company_id, credit_line.date_maturity or credit_line.date)

            if not credit_rate:
                continue

            partial_vals[rec.id] = {
                'partial_line_id': rec.id,
                'debit_name': debit_line.move_id.display_name,
                'debit_date': debit_line.move_id.date,
                'debit_rate': invoice_rate,
                'credit_name': credit_line.display_name,
                'credit_date': credit_line.date,
                'credit_date_maturity': credit_line.date_maturity,
                'credit_rate': credit_rate,
                'reconciled_amount': rec.amount,
                # we add exchange_diff_amount and variation_perc because is not computed on default computation.
                # TODO perhups on v12 can be removed
                'variation_perc': (credit_rate / invoice_rate - 1) * 100.0,
                'exchange_diff_amount': rec.company_id.currency_id.round(rec.amount * (credit_rate / invoice_rate - 1)),
            }
        return partial_vals

    @api.depends(
        'debit_move_id', 'credit_move_id', 'amount', 'exchange_diff_invoice_id.state', 'exchange_diff_ignored')
    def _compute_exchange_diff_adjustment_required(self):
        # for now only for out_invoices
        vals = self._get_partial_adjustment_vals()
        for rec in self:
            if not vals.get(rec.id, {}):
                rec.exchange_diff_adjustment_required = False
                continue
            exchange_diff_amount = vals.get(rec.id).get('exchange_diff_amount')

            allowed_perc = rec.company_id.exchange_diff_adjustment_tolerance
            credit_date_maturity = vals.get(rec.id).get('credit_date_maturity')
            if exchange_diff_amount and (exchange_diff_amount / rec.amount) > (allowed_perc / 100.0):
                rec.exchange_diff_adjustment_required = True
            # si no llegó la fecha de vencimiento marcamos como que requiere ajuste porque podria estar dentro de la
            # tolerancia pero llegada la fecha requerir ajuste
            elif credit_date_maturity and fields.Date.today() < credit_date_maturity:
                rec.exchange_diff_adjustment_required = True
            else:
                rec.exchange_diff_adjustment_required = False

    def unlink(self):
        recs = self.filtered('exchange_diff_invoice_id')
        if recs:
            raise UserError(_(
                'No puede desconciliar pagos que tienen una NC/ND de ajuste por diferencia de cambio.\n'
                'Si desea desvincular el pago deberá borrar/desvincular la/s NC/ND de ajuste (%s) de la/s facturas '
                'originales (%s)') % (
                    ', '.join(recs.mapped(lambda x: "%s [id: %s]" % (x.exchange_diff_invoice_id.display_name, x.exchange_diff_invoice_id.id))),
                    ', '.join(recs.mapped('debit_move_id.display_name')),
                ))
        return super().unlink()

# Intento de hacer que al cancelar conciliacion con ajuste de deuda, no se
# revierta si no que se cancele. Ibamos a probar hacer que genere los asientos
# y luego los borre pero no tenemos el link al reversal (que si viene en v12).
# Como tampoco es tan necesario por ahora no lo hacemos. TODO revisar en v12
# class AccountFullReconcile(models.Model):
#     _inherit = "account.full.reconcile"

#     def unlink(self):
#         to_reverse = self.mapped('exchange_move_id')
#         res = super(AccountFullReconcile, self).unlink()
#         to_reverse.button_cancel()
#         to_reverse.unlink()
#         # for rec in self.filtered('exchange_move_id'):
#         #     rec.exchange_move_id = False
#         #     aml = to_reverse.line_ids.filtered(lambda x: x.account_id.reconcile)
#         #     aml.reconciled = False
#         #     # aml.remove_move_reconcile()
#         #     # to_reverse.write()
#         #     # to_reverse.button_cancel()
#         #     to_reverse.unlink()
#         # return super(AccountFullReconcile, self).unlink()
#         return res
