##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################

from dateutil.relativedelta import relativedelta
import datetime
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PurchaseSubscription(models.Model):
    _name = "purchase.subscription"
    _description = "Purchase Subscription"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        required=True,
        track_visibility="always",
        default='New',
    )
    code = fields.Char(
        string="Reference",
        required=True,
        track_visibility="onchange",
        index=True,
        copy=False,
        default=lambda s: s.env['ir.sequence'].next_by_code(
            'purchase.subscription') or 'New',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string="Customer",
        required=True,
        auto_join=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda s: s.env['res.company']._company_default_get(),
        required=True,
    )
    tag_ids = fields.Many2many(
        'account.analytic.tag',
        string='Tags',
    )
    recurring_invoice_line_ids = fields.One2many(
        'purchase.subscription.line',
        'purchase_subscription_id',
        'Invoice Lines',
        copy=True,
    )
    recurring_total = fields.Float(
        compute='_compute_recurring_price',
        string="Recurring Price",
        store=True,
        track_visibility='onchange',
    )
    state = fields.Selection(
        [('draft', 'New'),
         ('open', 'In Progress'),
         ('pending', 'To Renew'),
         ('close', 'Closed'),
         ('cancel', 'Cancelled')],
        'Status',
        required=True,
        track_visibility='onchange',
        copy=False,
        default='draft',
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        'Analytic Account',
    )
    date_start = fields.Date(
        default=fields.Date.today,
    )
    date = fields.Date(
        'End Date',
        track_visibility='onchange',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.user.company_id.currency_id.id,
    )
    recurring_rule_type = fields.Selection(
        [('daily', 'Day(s)'),
         ('weekly', 'Week(s)'),
         ('monthly', 'Month(s)'), (
            'yearly', 'Year(s)'), ],
        'Recurrency',
        help="Invoice automatically repeat at specified interval",
        default='monthly',
    )
    recurring_interval = fields.Integer(
        'Repeat Every',
        help="Repeat every (Days/Week/Month/Year)",
        default=1
    )
    recurring_next_date = fields.Date(
        'Date of Next Invoice',
        default=fields.Date.today,
    )
    close_reason_id = fields.Many2one(
        "purchase.subscription.close.reason",
        "Close Reason",
        track_visibility='onchange',
    )
    description = fields.Text(
    )
    user_id = fields.Many2one(
        'res.users',
        'Responsible',
        track_visibility='onchange',
    )
    manager_id = fields.Many2one(
        'res.users',
        'Purchase Rep',
        track_visibility='onchange',
        help="It will be used to send the subcription reminder to expire",
    )
    invoice_count = fields.Integer(
        compute='_compute_invoice_count',
    )

    @api.depends('recurring_invoice_line_ids')
    def _compute_recurring_price(self):
        for account in self:
            account.recurring_total = sum(
                line.price_subtotal for line in account.
                recurring_invoice_line_ids)

    def set_open(self):
        return self.write({'state': 'open', 'date': False})

    def set_pending(self):
        return self.write({'state': 'pending'})

    def set_cancel(self):
        return self.write({'state': 'cancel'})

    def set_close(self):
        return self.write({
            'state': 'close',
            'date': fields.Date.from_string(fields.Date.today()),
        })

    def _compute_invoice_count(self):
        Invoice = self.env['account.move']
        for rec in self:
            rec.update({'invoice_count': Invoice.search_count(
                [('invoice_line_ids.purchase_subscription_id', '=', rec.id)])})

    def recurring_invoice(self):
        self._recurring_create_invoice()
        return self.action_subscription_invoice()

    @api.model
    def create(self, vals):
        if not vals.get('code', False):
            vals['code'] = self.env['ir.sequence'].next_by_code(
                'purchase.subscription') or 'New'
        if vals.get('name', 'New') == 'New':
            vals['name'] = vals['code']
        return super().create(vals)

    def _prepare_invoice_data(self):
        self.ensure_one()
        invoice = {}
        if not self.partner_id:
            raise UserError(_(
                "No Supplier Defined!\n"
                "You must first select a Supplier for "
                "Contract %s!") % self.name)

        partner = self.partner_id
        if 'force_company' in self.env.context:
            company = self.env['res.company'].browse(
                self.env.context['force_company'])
        else:
            company = self.company_id
            self = self.with_context(
                force_company=company.id,
                company_id=company.id
            )
        fpos = partner.property_account_position_id
        journals = self.env['account.journal'].search([
            ('type', '=', 'purchase'),
            ('company_id', '=', self.company_id.id)], limit=1)

        if not journals:
            raise UserError(_(
                'Please define a pruchase journal for the company "%s".') % (
                self.company_id.name or '', ))

        currency_id = self.currency_id.id

        invoice = {
            'type': 'in_invoice',
            'narration': "%s %s" % (self.name, fields.Date.from_string(
                self.recurring_next_date).strftime('%d-%m-%Y')),
            'partner_id': partner.id,
            'currency_id': currency_id,
            'journal_id': journals.id,
            'invoice_date': self.recurring_next_date,
            'invoice_origin': self.code,
            'fiscal_position_id': fpos.id,
            'company_id': company.id,
        }
        if partner.user_id:
            invoice.user_id = partner.user_id.id
        return invoice

    def _prepare_invoice_line(self, line, fiscal_position):
        if 'force_company' in self.env.context:
            company = self.env['res.company'].browse(
                self.env.context['force_company'])
        else:
            company = line.purchase_subscription_id.company_id
            line = line.with_context(
                force_company=company.id, company_id=company.id)

        account = line.product_id.property_account_expense_id
        if not account:
            account = line.product_id.\
                categ_id.property_account_expense_categ_id
        account_id = fiscal_position.map_account(account).id

        tax = line.product_id.supplier_taxes_id.filtered(
            lambda r: r.company_id == company)
        tax = fiscal_position.map_tax(
            tax, product=line.product_id, partner=self.partner_id)
        return {
            'name': line.name,
            'account_id': account_id,
            'analytic_account_id': line.purchase_subscription_id.analytic_account_id.id,
            'purchase_subscription_id': line.purchase_subscription_id.id,
            'price_unit': line.price_unit or 0.0,
            'discount': line.discount,
            'quantity': line.quantity,
            'product_uom_id': line.uom_id.id,
            'product_id': line.product_id.id,
            'tax_ids': [(6, 0, tax.ids)],
            'analytic_tag_ids': [
                (6, 0, line.purchase_subscription_id.tag_ids.ids)]
        }

    def _prepare_invoice_lines(self, fiscal_position):
        self.ensure_one()
        fiscal_position = self.env['account.fiscal.position'].browse(
            fiscal_position)
        return [(0, 0, self._prepare_invoice_line(line, fiscal_position))
                for line in self.recurring_invoice_line_ids]

    @api.model
    def _cron_recurring_create_invoice_purchase(self):
        return self._recurring_create_invoice(automatic=True)

    def _prepare_invoice(self):
        invoice = self._prepare_invoice_data()
        invoice['invoice_line_ids'] = self._prepare_invoice_lines(invoice['fiscal_position_id'])
        return invoice

    def _recurring_create_invoice(self, automatic=False):
        auto_commit = self.env.context.get('auto_commit', True)
        cr = self.env.cr
        invoices = self.env['account.move']
        current_date = datetime.date.today()
        if len(self) > 0:
            subscriptions = self
        else:
            domain = [('recurring_next_date', '<=', current_date),
                      ('state', 'in', ['open', 'pending'])]
            subscriptions = self.search(domain)
        if subscriptions:
            sub_data = subscriptions.read(fields=['id', 'company_id'])
            for company_id in set(data['company_id'][0] for data in sub_data):
                sub_ids = [s['id']
                           for s in sub_data
                           if s['company_id'][0] == company_id]
                subs = self.with_context(
                    company_id=company_id,
                    force_company=company_id).browse(sub_ids)
                context_company = dict(
                    self.env.context,
                    company_id=company_id, force_company=company_id)
                for subscription in subs:
                    if automatic and auto_commit:
                        cr.commit()  # pylint: disable=invalid-commit
                    try:
                        invoice_values = subscription.with_context(
                            lang=subscription.partner_id.lang).\
                            _prepare_invoice()
                        new_invoice = self.env['account.move'].with_context(
                            context_company).create(invoice_values)
                        new_invoice.message_post_with_view(
                            'mail.message_origin_link',
                            values={
                                'self': new_invoice, 'origin': subscription},
                            subtype_id=self.env.ref('mail.mt_note').id)
                        invoices += new_invoice
                        next_date = subscription.recurring_next_date or current_date
                        periods = {'daily': 'days', 'weekly': 'weeks',
                                   'monthly': 'months', 'yearly': 'years'}
                        invoicing_period = relativedelta(
                            **{periods[subscription.
                                       recurring_rule_type]:
                               subscription.recurring_interval})
                        new_date = next_date + invoicing_period
                        subscription.write(
                            {'recurring_next_date': new_date.
                             strftime('%Y-%m-%d')})
                        if automatic and auto_commit:
                            cr.commit()  # pylint: disable=invalid-commit
                    except Exception:
                        if automatic and auto_commit:
                            cr.rollback()
                            _logger.exception(
                                'Fail to create recurring invoice'
                                ' for subscription %s', subscription.code)
                        else:
                            raise
        return invoices

    @api.onchange('partner_id')
    def on_change_partner(self):
        currency_id = self.\
            partner_id.property_purchase_currency_id.id or self.\
            env.user.company_id.currency_id.id
        self.currency_id = currency_id

    def name_get(self):
        res = []
        for sub in self:
            name = '%s - %s' % (
                sub.code,
                sub.partner_id.name) if sub.code else sub.partner_id.name
            res.append((sub.id, name))
        return res

    def action_subscription_invoice(self):
        self.ensure_one()
        invoices = self.env['account.move'].search(
            [('invoice_line_ids.purchase_subscription_id', 'in', self.ids)])
        action = self.env.ref('account.action_move_in_invoice_type').read()[0]
        action["context"] = {"create": False}
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref(
                'purchase.view_move_form_inherit_purchase').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.model
    def cron_account_analytic_account(self):
        remind = {}

        def fill_remind(key, domain, write_pending=False):
            base_domain = [
                ('partner_id', '!=', False),
                ('manager_id', '!=', False),
                ('manager_id.email', '!=', False),
            ]
            base_domain.extend(domain)
            accounts = self.search(base_domain, order='name asc')
            for account in accounts:
                if write_pending:
                    account.write({'state': 'pending'})
                remind_user = remind.setdefault(account.manager_id.id, {})
                remind_type = remind_user.setdefault(key, {})
                remind_type.setdefault(
                    account.partner_id, []).append(account)

        # Already expired
        fill_remind("old", [('state', 'in', ['pending'])])

        # Expires now
        fill_remind("new", [('state', 'in', ['draft', 'open']),
                            '&', ('date', '!=', False),
                            ('date', '<=', datetime.date.today()),
                            ], True)

        # Expires in less than 30 days
        fill_remind("future", [
            ('state', 'in', ['draft', 'open']),
            ('date', '!=', False),
            ('date', '<', (datetime.datetime.today() + datetime.timedelta(30)))])
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        action_id = self.env.ref(
            'purchase_subscription.purchase_subscription_action').id
        template_id = self.env.ref(
            'purchase_subscription.purchase_account_analytic_cron_email_template').id
        for user_id, data in remind.items():
            _logger.debug("Sending reminder to uid %s", user_id)
            self.env['mail.template'].browse(template_id).with_context(
                base_url=base_url, action_id=action_id, data=data).send_mail(
                user_id, force_send=True)
        return True
