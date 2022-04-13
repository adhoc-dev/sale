# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import re

from datetime import date, datetime

from odoo import models, fields, api, _

from odoo.exceptions import ValidationError, UserError

class AccountBatchPayment(models.Model):
    _inherit = 'account.batch.payment'

    def _get_methods_generating_files(self):
        rslt = super(AccountBatchPayment, self)._get_methods_generating_files()
        rslt.append('bank')
        return rslt

    def validate_batch(self):
        if self.payment_method_code == 'bank':
            company = self.env.company

            if not company.galicia_creditor_identifier:
                raise UserError(_("Your company must have a creditor identifier in order to issue Galicia Automatic Debit payments requests. It can be defined in accounting module's settings."))

        return super(AccountBatchPayment, self).validate_batch()


    def galicia_txt_content(self, data_references):
        self.ensure_one()

        # build txt file
        content = ''

        #REGISTRO HEADER

        # tipo de registro
        content += '00'

        # nro de prestación, esto se saca de Ajustes > Configuración
        content += '%06d' % int(self.env.user.company_id.galicia_creditor_identifier)

        # servicio
        content += 'C'

        # fecha de generación
        content += str(datetime.now().strftime("%Y%m%d"))

        # identificación del archivo
        content += '3'

        # origen
        content += 'EMPRESA'

        # importe total
        content += '%014d' % int(re.sub('[^0-9]', '',str(self.amount)))

        # cantidad de registros
        content += '%07d' % len(self.payment_ids)

        #libre
        #content.rjust(304, " ") #VERIFICAR SI ES NECESARIO

        content += '\r\n'

        for rec in self.payment_ids: # seguramente tenga que poner algún filtro al self'

            # Tipo de registro
            content += data_references['record_type']

            # Identificación del cliente
            content += rec.partner_id.vat.ljust(22)

            # CBU
            if len(rec.partner_id.commercial_partner_id.bank_ids) == 0:
                raise ValidationError(f"El partner {rec.partner_id.commercial_partner_id.name} no tiene cuentas bancarias asociadas")
            cbu = rec.partner_id.commercial_partner_id.bank_ids[0].acc_number
            content += '0' + cbu[0:8] + '000' + cbu[8::]

            # REFERENCIA UNÍVOCA --> CREO QUE HABRÍA QUE TOMAR EL DATO DE UN WIZARD
            #pongo cualquier cosa solo para continuar con la prueba, dps borrar
            content += data_references['reference_payment'].ljust(15)

            # FECHA PRIMER VENCIMIENTO ---> CREO QUE HABRÍA QUE TOMAR EL DATO DEL WIZARD
            content += str(data_references['first_expiration_date'].strftime("%Y%m%d"))

            # IMPORTE
            content += '%014d' % int(re.sub('[^0-9]', '',str(rec.amount)))

            # EL RESTO
            content += '000000000000000000000000000000000000000000000   000000000000000                      0000000000000000000000000000000000000000'

            content += '\r\n'

        # REGISTRO TRAILER

        # tipo de registro
        content += '99'

        # nro de prestación
        content += '%06d' % int(self.env.user.company_id.galicia_creditor_identifier)

        # servicio
        content += 'C'

        # fecha de generación
        content += str(datetime.now().strftime("%Y%m%d"))

        # identificación del archivo
        content += '3'

        # origen
        content += 'EMPRESA'

        # importe total
        content += '%014d' % int(re.sub('[^0-9]', '',str(self.amount)))

        # cantidad de registros
        content += '%07d' % len(self.payment_ids)

        return [{
            'txt_filename': 'galicia.txt',
            #'txt_filename': 'SICORE_%s_%s_%s.txt' % (
            #     re.sub(r'[^\d\w]', '', self.company_id.name),
            #     self.from_date, self.to_date),
            'txt_content': content}]


        print(f"-----------CONTENIDO \n{content}")
