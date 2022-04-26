# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from datetime import datetime

from odoo import models, fields, _

from odoo.exceptions import UserError


class AccountBatchPayment(models.Model):
    _inherit = 'account.batch.payment'

    periodo = fields.Char()

    def galicia_debito_txt(self):
        if not self.journal_id.direct_debit_merchant_number or not self.direct_debit_collection_date:
            raise UserError(_('Debe tener indicado el numero de prestación en el diario con nombre "{self.journal_id.name}", id: {self.journal_id.id} y también el campo Collection date en el pago por lotes'))
        self.ensure_one()

        # build txt file
        content = ''

        # REGISTRO HEADER

        # tipo de registro
        content += '00'

        # nro de prestación, ver con jjs de cambiar el string a "Nro de prestación"
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

        for rec in self.payment_ids:

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
            cbu = rec.direct_debit_mandate_id.partner_bank_id.acc_number
            content += '0' + cbu[0:8] + '000' + cbu[8::]
            # CONCEPTO DE LA COBRANZA: es la referencia que identifica univocamente a la factura
            # cuando creamos pagos desde una factura automáticamente ya les estamos poniendo como "communication"
            # el nro de factura. Si algun cliente quiere que vaya numero de suscripcion con mes o algo por el estilo
            # deberia personalizarse para que se setee dicho dato en "communication"
            # TODO en v15 cambiar a "rec.ref or rec.name"

            content += (rec.communication[:4] + rec.communication[8:]).ljust(15) or rec.name[5:].ljust(15)

            # FECHA PRIMER VENCIMIENTO
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

    def master_credito_txt(self):
        self.ensure_one()

        #ver con jjs, creo que no haría falta en credito_master la validación para self.direct_debit_collection_date
        if not self.journal_id.direct_debit_merchant_number:
            raise UserError(_(f'Debe completar el numero de comercio en el diario con nombre "{self.journal_id.name}", id: {self.journal_id.id}'))

        if not self.periodo:
            raise UserError(_(f'Debe indicar el periodo con formato MM/AA'))

        content = ''

        # ENCABEZADO
        # nro de comercio
        content += self.journal_id.direct_debit_merchant_number.ljust(8)

        # Tipo de registro
        content += '1'

        # Fecha presentación
        content += self.date.strftime("%d%m")
        content += self.date.strftime("%Y")[-2:]
        # cantidad de registros
        content += '%07d' % len(self.payment_ids)

        # signo
        if self.amount > 0:
            content += '0'
        else:
            content += '-'

        #importe, es importante hacerlo así porque si termina con ".00" le deja un solo decimal
        importe_total = '%015.2f' % abs(self.amount)
        content += re.sub('[.]', '', importe_total)
        #filler
        content += ' '*91

        content += '\n'

        for rec in self.payment_ids:
            # nro de comercio
            content += self.journal_id.direct_debit_merchant_number.ljust(8)
            # tipo de comercio
            content += '2'

            # nro tarjeta
            content += '%016d' % int(rec.direct_debit_mandate_id.credit_card_number)

            # nro referencia, ver con jjs
            content += (rec.name[-12:] or '%012d' % int(re.sub('[^0-9]', '', rec.move_name)[:12])).ljust(12)

            # nro de cuota
            content += '001'

            # cuotas plan
            content += '999'

            # frecuencia db
            content += '01'

            #importe, es importante hacerlo así porque si termina con ".00" le deja un solo decimal
            monto = '%012.2f' % rec.amount
            content += re.sub('[.]', '', monto)

            # periodo, ver con jjs si tengo que validar que sea xx/xx (donde xx son numéros)
            content += self.periodo

            #filler
            content += ' '*67

            content += '\n'

        return [{
            'txt_filename': 'master_credito.txt',
            'txt_content': content}]

    def visa_credito_txt(self):
        self.ensure_one()
        if not self.journal_id.direct_debit_merchant_number:
            raise UserError(_(f'Debe completar el numero de establecimiento (10 dígitos) en el diario con nombre "{self.journal_id.name}", id: {self.journal_id.id}'))
        content = ''

        # ENCABEZADO
        # tipo de registro
        content += '0'
        content += 'DEBLIQC '

        # nro de establecimiento
        content += self.journal_id.direct_debit_merchant_number
        content += '900000    '

        # fecha de generación del archivo
        content += self.date.strftime("%Y%m%d")

        # hora generación archivo
        content += datetime.now().strftime("%H%M")

        # tipo de archivo. Débitos a liquidar
        content += '0'

        # estado archivo
        content += '  '

        # reservado
        content += ' '*55

        # marca fin de registro
        content += '*'

        content += '\n'

        ref = 1

        for rec in self.payment_ids:
            # tipo de registro
            content+='1'

            # numero de tarjeta
            content += '%016d' % int(rec.direct_debit_mandate_id.credit_card_number)

            # Reservado
            content += '   '

            # Referencia
            content += '%08d' % ref++

            # fecha de origen o vencimiento del débito
            content += self.date.strftime("%Y%m%d")

            # código de transacción
            content += '0005'

            #importe
            content += '%015.2f' % rec.amount

        return [{
            'txt_filename': 'visa_credito.txt',
            'txt_content': content}]

    def generate_debit_txt(self):
        if self.journal_id.direct_debit_format == 'cbu_galicia':
            contenido = self.galicia_debito_txt()
        if self.journal_id.direct_debit_format == 'master_credito':
            contenido = self.master_credito_txt()
        if self.journal_id.direct_debit_format == 'visa_credito':
            contenido = self.visa_credito_txt()
        res = self.env['download_files_wizard'].action_get_files(contenido)
        return res
