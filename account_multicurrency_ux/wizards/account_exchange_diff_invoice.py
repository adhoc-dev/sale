##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import formatLang, format_date


class AccountExchangeDiffInvoice(models.TransientModel):
    _name = 'account.exchange_diff_invoice'
    _description = 'account.exchange_diff_invoice'

    line_ids = fields.One2many(
        'account.exchange_diff_invoice.line',
        'wizard_id',
        string="Imputaciones para ajustar",
    )
    company_id = fields.Many2one(
        'res.company',
    )
    company_currency_id = fields.Many2one(
        related="company_id.currency_id",
        readonly=True,
    )
    invoice_ids = fields.Many2many(
        'account.move',
        string='NC/ND a validar',
        readonly=True,
        help='NC/ND que se crearon pero todavía no se validaron. Debe validarlas o borrarlas para generar una nueva NC/ND de ajuste',
    )
    exchange_diff_amount = fields.Monetary(
        compute="_compute_exchange_diff_amount",
        currency_field='company_currency_id',
        string="Ajuste",
    )

    @api.depends('line_ids.exchange_diff_amount',)
    def _compute_exchange_diff_amount(self):
        for rec in self:
            rec.exchange_diff_amount = sum(rec.line_ids.mapped('exchange_diff_amount'))

    @api.model
    def default_get(self, fct_fields):
        res = super().default_get(fct_fields)
        active_model = self._context.get('active_model')
        rec_ids = self._context.get('active_ids')
        if active_model == 'account.move':
            invoices = self.env['account.move'].browse(rec_ids)
            if len(invoices.mapped('commercial_partner_id')) != 1:
                raise ValidationError(_('Todas las facturas seleccionadas deben ser de la misma empresa.'))
            if len(invoices.mapped('company_id')) != 1:
                raise ValidationError(_('Todas las facturas seleccionadas deben ser de la misma compañía.'))
            partial_lines = invoices.mapped('line_ids.matched_credit_ids')
            company = invoices.mapped('company_id')
        elif active_model == 'account.payment.group':
            pay_groups = self.env['account.payment.group'].browse(rec_ids)
            partial_lines = pay_groups.move_line_ids.mapped('matched_debit_ids')
            company = pay_groups.company_id
        else:
            raise ValidationError(_('Exchange Difference Wizard must be called from an invoice or payment'))

        partial_vals = partial_lines.filtered(lambda x: x.exchange_diff_adjustment_required and not x.exchange_diff_invoice_id)._get_partial_adjustment_vals()
        to_validate = partial_lines.filtered(lambda x: x.exchange_diff_invoice_id.state not in ['posted']).mapped('exchange_diff_invoice_id')
        res.update({
            'line_ids': [(0, 0, x) for x in partial_vals.values()],
            'invoice_ids': [(6, 0, to_validate.ids)],
            'company_id': company.id,
        })
        return res

    def confirm(self):
        self.ensure_one()

        if self.exchange_diff_amount > 0.0:
            account_id = self.company_id.income_currency_exchange_account_id
            invoice_type = 'out_invoice'
        else:
            account_id = self.company_id.expense_currency_exchange_account_id
            invoice_type = 'out_refund'

        debit_line = self.line_ids[0].partial_line_id.debit_move_id
        company_currency_id = self.company_currency_id

        message = "".join(self.line_ids.mapped(
            lambda x: "* %s (%s) /  %s (%s): %s * ((%.2f / %.2f) - 1) = %s\n" % (
                x.debit_name,
                format_date(self.env, x.debit_date),
                x.credit_name,
                format_date(self.env, x.credit_date),
                formatLang(self.env, x.reconciled_amount, currency_obj=company_currency_id),
                x.credit_rate,
                x.debit_rate,
                formatLang(self.env, x.exchange_diff_amount, currency_obj=company_currency_id),
                )))

        vals = {
            'ref': 'Ajuste por diferencia de cambio',
            'invoice_origin': ', '.join(self.line_ids.mapped('debit_name')),
            'journal_id': debit_line.journal_id.id,
            'user_id': debit_line.move_id.user_id.id,
            'partner_id': debit_line.move_id.partner_id.id,
            'company_id': self.company_id.id,
            'type': invoice_type,
            'invoice_line_ids': [(0, 0, {
                'account_id': account_id.id,
                'name': 'Ajuste por diferencia de cambio\n%s' % message,
                'price_unit': abs(self.exchange_diff_amount),
            })],
        }

        new_invoice = self.env['account.move'].with_context(
            force_company_id=self.company_id.id, company_id=self.company_id.id, internal_type='debit_note').create(vals)

        # por ahor no validamos para dar mas flexibilidad a cualquier ajuste necesario
        # new_invoice.post()
        self.line_ids.mapped('partial_line_id').write({'exchange_diff_invoice_id': new_invoice.id})
        action = self.env["ir.actions.actions"]._for_xml_id('account.action_move_out_invoice_type')
        action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
        action['res_id'] = new_invoice.id
        return action

    def ignore(self):
        partial_lines = self.mapped('line_ids.partial_line_id')
        partial_lines.write({'exchange_diff_ignored': True})
        for invoice in partial_lines.mapped('debit_move_id.move_id'):
            invoice.message_post(body='Se ha ignorado realizar NC/ND de ajuste por diferencia de cambio')
        return True


class AccountExchangeDiffInvoice(models.TransientModel):
    _name = 'account.exchange_diff_invoice.line'
    _description = 'account.exchange_diff_invoice.line'

    wizard_id = fields.Many2one(
        'account.exchange_diff_invoice',
        ondelete='cascade',
        required=True,
    )
    partial_line_id = fields.Many2one(
        'account.partial.reconcile',
        readonly=True,
    )
    debit_name = fields.Char(
        readonly=True,
    )
    debit_date = fields.Date(
        readonly=True,
    )
    debit_rate = fields.Float(
        # help="Tasa de cambio entre moneda de la factura y moneda de la compañía",
        readonly=True,
    )
    credit_name = fields.Char(
        readonly=True,
    )
    credit_date = fields.Date(
        readonly=True,
    )
    credit_date_maturity = fields.Date(
        string='Due date',
        readonly=True,
    )
    credit_rate = fields.Float(
        # string="Tasa",
        # help="Tasa de cambio entre moneda de la factura y moneda de la compañía",
    )
    company_currency_id = fields.Many2one(
        related='wizard_id.company_id.currency_id',
        readonly=True,
    )
    reconciled_amount = fields.Monetary(
        string="Importe",
        help="Importe en moneda de la compañía",
        currency_field='company_currency_id',
        readonly=True,
    )
    exchange_diff_amount = fields.Monetary(
        string="Diferencia de cambio",
        help="Importe en moneda de la compañía",
        currency_field='company_currency_id',
        compute='_compute_exchange_diff_amount',
        # readonly=True,
    )
    variation_perc = fields.Float(
        string='Var. %',
        help='Porcentaje de variación en la tasa de cambio',
        compute='_compute_exchange_diff_amount',
    )

    @api.depends('credit_rate', 'reconciled_amount', 'debit_rate')
    def _compute_exchange_diff_amount(self):
        for rec in self:
            rec.exchange_diff_amount = rec.company_currency_id.round(
                rec.reconciled_amount * (rec.credit_rate / rec.debit_rate - 1))
            rec.variation_perc = (rec.credit_rate / rec.debit_rate - 1) * 100.0

    @api.onchange('credit_rate')
    def _onchange_credit_rate(self):
        oficial_rate = self.partial_line_id.debit_move_id.currency_id._convert(
            1.0, self.wizard_id.company_id.currency_id, self.wizard_id.company_id,
            self.credit_date_maturity or self.credit_date)
        allowed_perc = self.wizard_id.company_id.exchange_rate_tolerance
        if abs(self.credit_rate - oficial_rate) / oficial_rate > (allowed_perc / 100.0):
            raise ValidationError(
                "No puede usar modificar la tasa de cambio en más de un %s%% "
                "del valor del sistema (%s en este caso)." % (allowed_perc, oficial_rate))
