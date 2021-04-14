##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################

from odoo import models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def whatsapp_redirect(self):
        number = self.env.context.get('number')
        return {
            'type': 'ir.actions.act_url',
            'url': "https://api.whatsapp.com/send?phone=%s" % number,
        }
