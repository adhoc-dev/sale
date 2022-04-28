##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################

from odoo import models, fields, api
import re


class ResPartner(models.Model):
    _inherit = 'res.partner'

    whatsapp_number = fields.Char(compute="_number_format")

    def whatsapp_redirect(self):
        return {
            'type': 'ir.actions.act_url',
            'url': "https://api.whatsapp.com/send?phone=%s" % self.whatsapp_number,
        }

    @api.depends('mobile')
    def _number_format(self):
        # Whatsapp expect international number format
        # All phone numbers in Argentina (country code "54") should have a "9" between the country code and area code.
        # The prefix "15" must be removed so the final number will have 13 digits total: +54 9 XXX XXX XXXX
        if self.mobile:
            match = re.match(r'(\+54)[ ]{0,1}(9){0,1}(.*)', self.mobile)
            if match:
                self.whatsapp_number = '54 9' + match.group(3)
                self.whatsapp_number = self.whatsapp_number.replace(' ', '').replace('-', '')
                if not len(self.whatsapp_number) == 13:
                    self.whatsapp_number = None
            else:
                self.whatsapp_number = self.mobile.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        else:
            self.whatsapp_number = None
