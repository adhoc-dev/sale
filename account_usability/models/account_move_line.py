# -*- coding: utf-8 -*-
# © 2016 ADHOC SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, fields
from collections import OrderedDict
from openerp.tools import float_compare, float_is_zero
# from openerp.exceptions import UserError, ValidationError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    account_user_type_id = fields.Many2one(
        string='Account Type',
        related='account_id.user_type_id',
        store=True,
        readonly=True,
    )
    analytic_tag_ids = fields.Many2many(
        related='analytic_account_id.tag_ids',
        readonly=True,
        string='Analytic Tags',
    )

    @api.multi
    def action_open_related_document(self):
        self.ensure_one()
        # usamos lo que ya se usa en js para devolver la accion
        res_model, res_id, action_name, view_id = self.get_model_id_and_name()

        return {
            'type': 'ir.actions.act_window',
            'name': action_name,
            'res_model': res_model,
            'view_type': 'form',
            'view_mode': 'form',
            'views': [[view_id, 'form']],
            'res_id': res_id,
            # 'view_id': res[0],
        }

    @api.multi
    def remove_move_reconcile(self):
        """
        Parche para que al desconciliar deuda que tiene algun asiento de ajuste
        por diferencia de cambio, este asiento, en vez de revertirse, se borre.
        Además esto borra un bug de odoo donde, por ejemplo, si concilio una
        factura en USD con dos pagos, y el último saldaba la deuda en ARS,
        luego odoo creaba asiento automático de ajuste pero no teníamos forma
        de desconciliarlo
        """
        if not self.env['ir.config_parameter'].sudo().get_param(
                'delete_exchange_rate_entry', False):
            return super(AccountMoveLine, self).remove_move_reconcile()
        # al querer borrar conciliación, antes de llamar a super, buscamos
        # todos los asientos de dif de cambio y les borramos el
        # rate_diff_partial_rec_id así odoo no los borra en el metodo unlink
        # de los partial reconcile
        rec_move_ids = self.env['account.partial.reconcile']
        for account_move_line in self:
            rec_move_ids += account_move_line.matched_debit_ids
            rec_move_ids += account_move_line.matched_credit_ids
        # este método lo copianos de odoo de los unlink de los part. reconcile
        exchange_rate_entries = self.env['account.move'].search(
            [('rate_diff_partial_rec_id', 'in', rec_move_ids.ids)])
        for rec in rec_move_ids:
            partial_rec_set = OrderedDict.fromkeys([rec])
            aml_set = self.env['account.move.line']
            total_debit = 0
            total_credit = 0
            total_amount_currency = 0
            currency = None
            for partial_rec in partial_rec_set:
                if currency is None:
                    currency = partial_rec.currency_id
                for aml in [
                        partial_rec.debit_move_id, partial_rec.credit_move_id]:
                    if aml not in aml_set:
                        total_debit += aml.debit
                        total_credit += aml.credit
                        aml_set |= aml
                        if aml.currency_id and aml.currency_id == currency:
                            total_amount_currency += aml.amount_currency
                    for x in aml.matched_debit_ids | aml.matched_credit_ids:
                        partial_rec_set[x] = None
            digits_rounding_precision = \
                aml_set[0].company_id.currency_id.rounding
            if float_compare(
                    total_debit, total_credit,
                    precision_rounding=digits_rounding_precision) == 0 \
                    or (currency and float_is_zero(total_amount_currency,
                        precision_rounding=currency.rounding)):
                # if the reconciliation is full, also unlink any currency rate
                # difference entry created
                exchange_rate_entries |= self.env['account.move'].search(
                    [('rate_diff_partial_rec_id', 'in',
                        [x.id for x in partial_rec_set.keys()])])
        exchange_rate_entries.write({'rate_diff_partial_rec_id': False})
        res = super(AccountMoveLine, self).remove_move_reconcile()
        # luego de llamar a super donde se borraron las conciliaciones y no se
        # hizo el reverso, entonces cancelamos el asiento, borramos los macheos
        # que quedan (sin llamar a remove_move_reconcile) porque se nos
        # hace recursivo, y luego borramos asiento
        exchange_rate_entries.button_cancel()
        # exchange_rate_entries.line_ids.remove_move_reconcile()
        rate_rec_move_ids = self.env['account.partial.reconcile']
        for account_move_line in exchange_rate_entries.line_ids:
            rate_rec_move_ids += account_move_line.matched_debit_ids
            rate_rec_move_ids += account_move_line.matched_credit_ids
        rate_rec_move_ids.unlink()
        exchange_rate_entries.unlink()
        return res
