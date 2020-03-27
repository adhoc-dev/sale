from odoo import api, fields, models


class SaleSubscriptionLine(models.Model):
    _inherit = "sale.subscription.line"

    purchase_price = fields.Float(
        string='Unit Cost', digits='Product Price',
        help="Amount needed to purchase one unit of this product",
        compute="_compute_purchase_price")

    @api.depends('product_id.standard_price',
                 'analytic_account_id.pricelist_id.currency_id',
                 'product_id.uom_id', 'uom_id')
    def _compute_purchase_price(self):
        lines = self.filtered(lambda x: x.product_id and x.analytic_account_id.pricelist_id and x.uom_id)
        (self - lines).update({'purchase_price': 0.0})
        for line in lines:

            # Get Currencies
            frm_cur = self.env.company.currency_id
            to_cur = line.analytic_account_id.pricelist_id.currency_id
            purchase_price = line.product_id.standard_price

            # Adjust cost if UOM is different than product's.
            if line.uom_id != line.product_id.uom_id:
                purchase_price = line.product_id.uom_id._compute_price(
                    purchase_price, line.uom_id)

            # Calculate price using subscription's curr. or company's curr.
            line.purchase_price = frm_cur._convert(
                purchase_price, to_cur,
                line.analytic_account_id.company_id or self.env.company,
                fields.Date.today(),
                round=True)


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    margin = fields.Monetary(
        'Margin',
        compute='_compute_margin',
        help="The difference between the recurring total and the sum of "
        "all costs in this subscription",
        currency_field='currency_id', digits='Product Price')

    profitability = fields.Float(
        'Profitability (%)',
        help="The ratio between the profit margin and "
        "the total price of this subscription",
        compute="_compute_margin", group_operator='avg')

    @api.depends(
        'recurring_total', 'recurring_invoice_line_ids.purchase_price',
        'recurring_invoice_line_ids.quantity')
    def _compute_margin(self):
        for subs in self:
            # Calculate the sum of the costs of each subs. line
            cost_total = sum(subs.recurring_invoice_line_ids.mapped(
                lambda x: x.purchase_price * x.quantity))

            # Calculate margin and profitability
            subs.margin = subs.recurring_total - cost_total
            subs.profitability = round(
                (subs.margin / subs.recurring_total) * 100, 2) if subs.recurring_total else 0
