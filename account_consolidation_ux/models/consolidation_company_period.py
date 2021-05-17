# -*- coding: utf-8 -*-

from odoo import models
from odoo.tools.safe_eval import safe_eval
from odoo.osv import expression


class ConsolidationCompanyPeriod(models.Model):
    _inherit = "consolidation.company_period"

    def _get_move_lines_domain(self, consolidation_account):
        """
        Get the domain definition to get all the move lines "linked" to this company period and a given consolidation
        account. That means all the move lines that :
        - are in the right company,
        - are not in excluded journals,
        - are linked to a account.account which is mapped in the given consolidation account
        - have a date contained in the company period start and company period end.
        :param consolidation_account: the consolidation account
        :return: a domain definition to be use in search ORM method.
        """
        self.ensure_one()
        domain = super()._get_move_lines_domain(consolidation_account)
        return expression.AND([safe_eval(consolidation_account.additional_domain), domain])
