##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
from odoo.tools.date_utils import get_timedelta
from odoo.exceptions import ValidationError
from odoo.tools import safe_eval


class SaleOrderLineValsFormula(models.Model):

    _name = "sale.order.line.vals_formula"
    _description = "Subscription Quantity Formula"

    name = fields.Char(required=True, translate=True)
    code = fields.Text(required=True, default="""
# Available variables:
# * env: current environment
# * line: recordset of the current sale.order.line being evaluated
# * subscription_start_date: first day of the period for this recurring invoice
# * subscription_end_date: last day of the period for this recurring invoice
# * previous_period_start_date: subscription_start_date less one subscription period
# * previous_period_end_date: subscription_end_date less one subscription period
# * datetime: safe_eval.datetime
# * dateutil: safe_eval.dateutil
# * time: safe_eval.time
# The code must return a dictorionary with the vals that should override the invoice line vals
result = {'quantity': line.qty_delivered or line.product_uom_qty}
    """)

    @api.constrains("code")
    def _check_code(self):
        line = self.env["sale.order.line"]
        subscription_start_date, subscription_end_date = self._get_dummy_dates(line)
        self._get_result(line, subscription_start_date, subscription_end_date)

    @api.model
    def _get_dummy_dates(self, line):
        subscription_start_date = line.order_id.next_invoice_date or line.order_id.start_date or fields.Datetime.today()
        subscription_end_date = subscription_start_date + get_timedelta(
            line.order_id.recurrence_id.duration or 1,
            line.order_id.recurrence_id.unit or 'month')
        return subscription_start_date, subscription_end_date

    def test_formula(self):
        line = self.env['sale.order.line'].browse(self._context.get('sale_line_id'))
        subscription_start_date, subscription_end_date = self._get_dummy_dates(line)
        # TODO ver de reutilizar codigo de _get_result
        previous_period_start_date = subscription_start_date + get_timedelta(
            -line.order_id.recurrence_id.duration or -1,
            line.order_id.recurrence_id.unit or 'month')
        previous_period_end_date = subscription_end_date + get_timedelta(
            -line.order_id.recurrence_id.duration or -1,
            line.order_id.recurrence_id.unit or 'month')
        if not line:
            raise ValidationError('No sale_line_id on context to test formula')
        raise ValidationError(_(
            'Result while evaluating formulawith:\n'
            '* Sale line Id: %s\n'
            '* Start date: %s\n'
            '* End date: %s\n'
            '* Previous Start date: %s\n'
            '* Previous End date: %s\n'
            '* Result: %s') % (
                line.id,
                subscription_start_date,
                subscription_end_date,
                previous_period_start_date,
                previous_period_end_date,
                self._get_result(line, subscription_start_date, subscription_end_date)))

    def _get_result(self, line, subscription_start_date, subscription_end_date):
        self.ensure_one()
        previous_period_start_date = subscription_start_date + get_timedelta(
            -line.order_id.recurrence_id.duration or -1,
            line.order_id.recurrence_id.unit or 'month')
        previous_period_end_date = subscription_end_date + get_timedelta(
            -line.order_id.recurrence_id.duration or -1,
            line.order_id.recurrence_id.unit or 'month')
        eval_context = {
            "env": self.env,
            "line": line,
            'subscription_start_date': subscription_start_date,
            'subscription_end_date': subscription_end_date,
            'previous_period_start_date': previous_period_start_date,
            'previous_period_end_date': previous_period_end_date,
            'datetime': safe_eval.datetime,
            'dateutil': safe_eval.dateutil,
            'time': safe_eval.time,
        }

        try:
            safe_eval.safe_eval(
                self.code.strip(),
                eval_context,
                mode="exec",
                nocopy=True,
            )
        except Exception as e:
            raise ValidationError(_("Error evaluating code: %s") % e)
        result = eval_context.get("result")
        if not result or type(result) is not dict:
            raise ValidationError(_(
                "The code should return a dictionary of the vals to be overridden on a variable called 'result'"))
        return result
