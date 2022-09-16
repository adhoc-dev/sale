##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, api, fields
from markupsafe import Markup
from odoo.tools import is_html_empty


class SaleSubscription(models.Model):

    _inherit = "sale.subscription"

    partner_id = fields.Many2one(check_company=True)
    partner_invoice_id = fields.Many2one(check_company=True)
    dates_required = fields.Boolean(
        related="template_id.dates_required",
    )
    use_different_invoice_address = fields.Boolean(
        related="template_id.use_different_invoice_address",
    )

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        # esto lo hacemos porque suele ser util poder buscar por cuenta
        # analitica
        args = args or []
        domain = [
            '|', '|', ('analytic_account_id', operator, name),
            ('code', operator, name), ('name', operator, name)]
        partners = self.env['res.partner'].search([('name', operator, name)], limit=limit)
        if partners:
            domain = ['|'] + domain + [('partner_id', 'in', partners.ids)]
        rec = self.search(domain + args, limit=limit)
        return rec.name_get()

    def _prepare_invoice_data(self):
        """ Copy the terms and conditions of the subscription as part of the
        invoice note. Also fix a core Odoo behavior to get payment terms.
        """
        res = super()._prepare_invoice_data()
        if not self.template_id.add_period_dates_to_description:
            narration = ""
            if not is_html_empty(self.description):
                narration = Markup('<br/>') + self.description
            elif self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms') and not is_html_empty(self.company_id.invoice_terms):
                narration += Markup('<br/>') + self.company_id.invoice_terms
            res.update({'narration': narration})
        if self.template_id.use_different_invoice_address and self.partner_invoice_id:
            res.update({'partner_id': self.partner_invoice_id.id})
        return res

    def update_lines_prices_from_products(self):
        """ Update subscription lines, all the line including prices.
        """
        for subscription in self:
            for line in subscription.recurring_invoice_line_ids:
                line.onchange_product_quantity()
            subscription._amount_all()
