##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class SaleOrderLineQuantityFormula(models.Model):

    _name = "sale.order.line.quantity.formula"
    _description = "Subscription Quantity Formula"

    name = fields.Char(required=True, translate=True)
    code = fields.Text(required=True, default="""
# Available variables:
# * env: current environment
# * line: recordset of the current sale.order.line being evaluated
# The code must return a dictorionary with the vals that should override the invoice line vals
result = {'quantity': line.qty_delivered or line.product_uom_qty}
    """)

    @api.constrains("code")
    def _check_code(self):
        self._get_result(self.env["sale.order.line"])

    def _get_result(self, line):
        self.ensure_one()
        eval_context = {
            "env": self.env,
            "line": line,
        }

        try:
            safe_eval(
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
