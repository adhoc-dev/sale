from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SDDMandate(models.Model):
    _inherit = 'account.direct_debit.mandate'

    credit_card_number = fields.Char(readonly=True, states={'draft': [('readonly', False)]},)
    partner_bank_id = fields.Many2one(
        'res.partner.bank', 'CBU', readonly=True, states={'draft': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        check_company=True,
        help="Account of the customer to collect payments from.")

    def action_validate_mandate(self):
        for rec in self:
            if rec.direct_debit_format in ('cbu_macro', 'cbu_galicia'):
                if not rec.partner_bank_id.acc_type == 'cbu':
                    raise UserError(_('A CBU account is requred for this mandate'))
            elif rec.direct_debit_format in ('visa_credito', 'master_credito', 'visa_debito'):
                if not rec.credit_card_number:
                    raise UserError(_('Credit Card Number is required for this mandate'))
        return super().action_validate_mandate()
