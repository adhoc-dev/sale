##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, api, fields


class AccountBatchPaymentWizard(models.TransientModel):
    _name = 'account.batch_payment.wizard'
    _description = 'account.batch_payment.wizard'

    reference_payment = fields.Char(string='Concepto de la cobranza', size=15, default="SUSCRIPCION")
    first_expiration_date = fields.Date(string='Fecha del primer vencimiento', required=True)
    record_type = fields.Selection([
        ('0370', 'Orden de débito enviada por la empresa'),
        ('0320', 'Reversión / anulación de débito'),
        ('0361', 'Rechazo de reversión'),
        ('0382', 'Adhesión'),
        ('0363', 'Rechazo de adhesión'),
        ('0385', 'Cambio de identificación')], string='Tipo de registro', required=True, default="0370")

    def action_confirm_galicia_txt_content(self):
        self.ensure_one()

        data_references = {
        'reference_payment': self.reference_payment,
        'first_expiration_date': self.first_expiration_date,
        'record_type': self.record_type
        }

        if self._context['active_model'] == 'account.batch.payment':
            txt = self.env['account.batch.payment'].browse(self._context['active_id']).galicia_txt_content(data_references)
            return self.env['download_files_wizard'].action_get_files(txt)
