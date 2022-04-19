# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import re

from datetime import date, datetime

from odoo import models, fields, api, _

from odoo.exceptions import ValidationError, UserError


class AccountBatchPayment(models.Model):
    _inherit = 'account.batch.payment'

    periodo = fields.Char()

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

    def _galicia_txt_content(self):
        if not self.journal_id.direct_debit_merchant_number or not self.direct_debit_collection_date:
            raise UserError(_('Debe completar los campos bla bla y bla bla'))
        self.ensure_one()

        # build txt file
        content = ''

        # REGISTRO HEADER

        # tipo de registro
        content += '00'

        # nro de prestación, esto se saca de Ajustes > Configuración
        content += '%06d' % int(self.journal_id.direct_debit_merchant_number)

        # servicio
        content += 'C'

        # fecha de generación
        content += datetime.now().strftime("%Y%m%d")

        # identificación del archivo
        content += '3'

        # origen (EMPRESA O BANCO)
        content += 'EMPRESA'

        # importe total
        content += '%014d' % int(re.sub('[^0-9]', '', str(self.amount)))

        # cantidad de registros
        content += '%07d' % len(self.payment_ids)

        # libre
        # content.rjust(304, " ") #VERIFICAR SI ES NECESARIO

        content += '\r\n'

        for rec in self.payment_ids:  # seguramente tenga que poner algún filtro al self'

            # Tipo de registro
            # TODO ver si implementamos otros, por ahora solo 0370
            # ('0370', 'Orden de débito enviada por la empresa'),
            # ('0320', 'Reversión / anulación de débito'),
            # ('0361', 'Rechazo de reversión'),
            # ('0382', 'Adhesión'),
            # ('0363', 'Rechazo de adhesión'),
            # ('0385', 'Cambio de identificación')
            content += '0370'

            # Identificación del cliente
            content += rec.partner_id.vat.ljust(22)

            # CBU
            if len(rec.partner_id.commercial_partner_id.bank_ids) == 0:
                raise ValidationError(f"El partner {rec.partner_id.commercial_partner_id.name} no tiene cuentas bancarias asociadas")
            # TODO: cambiar a usar en mandate
            cbu = rec.partner_id.commercial_partner_id.bank_ids[0].acc_number
            content += '0' + cbu[0:8] + '000' + cbu[8::]

            # CONCEPTO DE LA COBRANZA: es la referencia que identifica univocamente a la factura
            # cuando creamos pagos desde una factura automáticamente ya les estamos poniendo como "communication"
            # el nro de factura. Si algun cliente quiere que vaya numero de suscripcion con mes o algo por el estilo
            # deberia personalizarse para que se setee dicho dato en "communication"
            # TODO en v15 cambiar a "rec.ref or rec.name"
            content += (rec.communication or rec.name).ljust(15)

            # FECHA PRIMER VENCIMIENTO ---> CREO QUE HABRÍA QUE TOMAR EL DATO DEL WIZARD
            content += self.direct_debit_collection_date.strftime("%Y%m%d")

            # IMPORTE
            content += '%014d' % int(re.sub('[^0-9]', '', str(rec.amount)))

            # EL RESTO
            content += '000000000000000000000000000000000000000000000   000000000000000                      0000000000000000000000000000000000000000'

            content += '\r\n'

        # REGISTRO TRAILER

        # tipo de registro
        content += '99'

        # nro de prestación
        content += '%06d' % int(self.journal_id.direct_debit_merchant_number)

        # servicio
        content += 'C'

        # fecha de generación
        content += datetime.now().strftime("%Y%m%d")

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
            'txt_content': content}]


        print(f"-----------CONTENIDO \n{content}")

    def _credito_master(self):
        self.ensure_one()

        if not self.journal_id.direct_debit_merchant_number or not self.direct_debit_collection_date:
            raise UserError(_('Debe completar los campos bla bla y bla bla'))

        content = ''
        content += '00'

        for rec in self.payment_ids:
            # nro de comercio, esto se saca de Ajustes > Configuración
            content += '%06d' % int(self.journal_id.direct_debit_merchant_number)

            # tipo de comercio
            content += '2'

            # nro tarjeta
            content += '%016d' % int(self.payment_ids.direct_debit_mandate_id.credit_card_number)

            # nro referencia
            content += '%012d' % int(re.sub('[^0-9]', '', self.payment_ids.move_name)[:12])

            # nro de cuota
            content += '001'

            # cuotas plan
            content += '999'

            # periodo
            content += self.periodo
            # frecuencia db
            content += '01'

            print(f"----{content}")
            content += '\n'
        return [{
            'txt_filename': 'credito_master.txt',
            #'txt_filename': 'SICORE_%s_%s_%s.txt' % (
            #     re.sub(r'[^\d\w]', '', self.company_id.name),
            #     self.from_date, self.to_date),
            'txt_content': content}]

    def _generate_export_file(self):
        if self.direct_debit_format == 'galicia':
            return self._galicia_txt_content()
        elif self.direct_debit_format == 'master':
            return self._credito_master()
        # TODO adaptar ambos metodos para que devuelvan un diccionario similar a esto
            # payments = self.payment_ids.sorted(key=lambda r: r.id)
            # payment_dicts = self._generate_payment_template(payments)
            # xml_doc = self.journal_id.create_iso20022_credit_transfer(payment_dicts, self.sct_batch_booking, self.sct_generic)
            # return {
            #     'file': base64.encodebytes(xml_doc),
            #     'filename': "SCT-" + self.journal_id.code + "-" + datetime.now().strftime('%Y%m%d%H%M%S') + ".xml",
            # }

        return super()._generate_export_file()
