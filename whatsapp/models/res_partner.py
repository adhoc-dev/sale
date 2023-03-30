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
        for rec in self:
            if rec.mobile:
                match = re.match(r'(\+54)[ ]{0,1}(9){0,1}(.*)', rec.mobile)
                if match:
                    rec.whatsapp_number = '54 9' + match.group(3)
                    rec.whatsapp_number = rec.whatsapp_number.replace(' ', '').replace('-', '')
                    if not len(rec.whatsapp_number) == 13:
                        rec.whatsapp_number = None
                else:
                    rec.whatsapp_number = rec.mobile.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            else:
                rec.whatsapp_number = None
