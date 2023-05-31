from odoo import models, fields


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    helpdesk_ticket_id = fields.Many2one(domain="[('project_id', '=?', project_id)]")

    def _timesheet_preprocess(self, vals):
        vals = super(AccountAnalyticLine, self)._timesheet_preprocess(vals)
        helpdesk_ticket_id = vals.get('helpdesk_ticket_id')
        if helpdesk_ticket_id:
            ticket = self.env['helpdesk.ticket'].browse(helpdesk_ticket_id)
            if ticket.analytic_account_id and ticket.analytic_account_id.company_id:
                vals.update({
                    'company_id': ticket.analytic_account_id.company_id.id,
                })
        return vals
