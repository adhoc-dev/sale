from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    direct_debit_mandate_ids = fields.One2many('account.direct_debit.mandate', 'commercial_partner_id')
    dd_count = fields.Integer(compute='_compute_dd_count', string="DD count")

    def _compute_dd_count(self):
        sdd_data = self.env['account.direct_debit.mandate'].read_group(
            domain=[('commercial_partner_id', 'in', self.ids), ('state', '=', 'active')],
            fields=['commercial_partner_id'],
            groupby=['commercial_partner_id'])
        mapped_data = dict([(m['commercial_partner_id'][0], m['commercial_partner_id_count']) for m in sdd_data])
        for partner in self:
            partner.dd_count = mapped_data.get(partner.id, 0)
