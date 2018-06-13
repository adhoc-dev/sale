##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models


class HelpdeskSolutionTag(models.Model):

    _name = 'helpdesk.solution.tag'
    _description = "Helpdesk Solution Tag"

    name = fields.Char(
        required=True,
    )

    color = fields.Integer(
        'Color Index',
    )

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]
