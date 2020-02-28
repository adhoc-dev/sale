##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models


class HelpdeskSolutionFaqCategory(models.Model):

    _name = 'helpdesk.solution.faq.category'
    _description = "Helpdesk Solution Faq Category"

    name = fields.Char(
        required=True,
    )

    color = fields.Integer(
        'Color Index',
    )

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Faq Category name already exists !"),
    ]
