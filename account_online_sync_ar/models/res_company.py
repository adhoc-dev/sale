from odoo import fields, models


class ResCompany(models.Model):

    _inherit = 'res.company'

    paybook_user_id = fields.Char("Paybook User ID")
    paybook_api_key = fields.Char("Paybook API KEY", groups="saas_client.group_saas_support")
