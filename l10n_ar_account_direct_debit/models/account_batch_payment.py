import re
import base64
from datetime import datetime

from odoo import models, fields, api

from odoo.exceptions import UserError


class AccountBatchPayment(models.Model):
    _inherit = 'account.batch.payment'

    periodo = fields.Char()

    @api.model
    def _get_reference(self, payment, lenght, onlydigits=False):
        """ Metodo utilizado para obtener la referencia de un pago. Intentamos buscar el valor en el campo
        communication (en v15 ref), si no esta seteado se usa el name (numero/nombre del pago).
        Si un cliente quiere un valor particular (nro de suscripcion, nro de factura, nro de recibo), entonces se
        debe implementar que al campo communication vaya dicho numero"""
        # usamos el name que si se usa account_payment_group va a ser el nro de recibo. Eventualmente podríamos hacerlo opcional en algun lugar y que tome name o payment.communication
        ref = payment.name
        if onlydigits:
            ref = ''.join(i for i in ref if i.isdigit())
        return ref[-lenght:].ljust(lenght)

    def _galicia_debito_txt(self):
        if not self.journal_id.direct_debit_merchant_number or not self.direct_debit_collection_date:
            raise UserError(
                'Debe tener indicado el numero de prestación en el diario con nombre %s, id: %s y también el campo '
                'Collection date en el pago por lotes' % (self.journal_id.name, self.journal_id.id))
        self.ensure_one()

        # build txt file
        content = ''

        # REGISTRO HEADER

        # tipo de registro
        content += '00'

        # nro de prestación
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
        content += ' '*304

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
            content += (rec.partner_id.vat or '').ljust(22)

            # CBU
            cbu = rec.direct_debit_mandate_id.partner_bank_id.acc_number
            content += '0' + cbu[0:8] + '000' + cbu[8:]

            # CONCEPTO DE LA COBRANZA: es la referencia que identifica univocamente a la factura
            content += self._get_reference(rec, 15, onlydigits=False)

            # FECHA PRIMER VENCIMIENTO
            content += self.direct_debit_collection_date.strftime("%Y%m%d")

            # IMPORTE
            content += '%014d' % int(re.sub('[^0-9]', '', str(rec.amount)))

            # EL RESTO
            content += '000000000000000000000000000000000000000000000   000000000000000                      0000000000000000000000000000000000000000'

            # libre
            content += ' '*136

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

        # libre
        content += ' '*304

        return content

    def _macro_cbu(self):
        self.ensure_one()
        content = ''
        if not self.journal_id.direct_debit_merchant_number or not self.direct_debit_collection_date:
            raise UserError(
                'Debe tener indicado el numero de convenio en el diario con nombre %s, id: %s y también el campo '
                'Collection date que representa la fecha de vencimiento' % (self.journal_id.name, self.journal_id.id))

        # ENCABEZADO
        # Filler
        content += '1'

        # Nro de convenio (longitud 5)
        content += self.journal_id.direct_debit_merchant_number[:5].ljust(5)

        # Nro de servicio
        content += ' '*10

        # Nro de empresa de sueldos
        content += '0'*5

        # Fecha de generación de archivo
        content += self.date.strftime("%Y%m%d")

        # importe total de movimientos
        content += ('%019.2f' % self.amount).replace('.','')

        # moneda de la empresa
        if self.env.company.currency_id.name == 'ARS':
            content += '080'
        elif self.env.company.currency_id.name == 'USD':
            content += '002'

        # tipo de movimientos del archivo
        content += '01'

        # información monetaria
        content += '0'*98

        # sin uso
        content += ' '*69

        # filler
        content += '0'

        content += '\n'

        for rec in self.payment_ids:
            # filler
            content += '0'

            # nro convenio, longitud 5
            content += self.journal_id.direct_debit_merchant_number[:5].ljust(5)

            # nro de servicio
            content += ' '*10

            # nro de empresa de sueldos
            content += '0'*5

            # código de banco del adherente y código de sucursal de la cuenta
            content += rec.direct_debit_mandate_id.partner_bank_id.acc_number[:7]

            # tipo de cuenta (por ahora consideramos que todos son CBU sin importar el banco)
            # (3 - Cta. Cte. ,  4 - Caja de Ahorros para cuentas de Banco Macro - Bansud. Para cuentas de otros bancos no informar)
            content += ' '

            # cuenta bancaria del adherente
            content += '%015d' % int(rec.direct_debit_mandate_id.partner_bank_id.acc_number[9:])

            # identificación del adherente
            if not rec.partner_id.vat:
                raise UserError(
                    'El partner %s con id %s debe tener número de identificación' % (
                        self.partner_id.name, self.partner_id.id))
            content += (rec.partner_id.vat or '').ljust(22)

            # identificación del débito
            content += self._get_reference(rec, 15, onlydigits=False)

            # blancos
            content += ' '*6

            # fecha de vencimiento
            content += self.direct_debit_collection_date.strftime("%Y%m%d")

            # moneda del débito
            if rec.currency_id.name == 'ARS':
                content += '080'
            elif rec.currency_id.name == 'USD':
                content += '002'

            # importe a debitar
            content += ('%014.2f' % rec.amount).replace('.','')

            # ceros y espacios
            content += '0'*41 + ' '*67 + '0'
            content += '\n'

        return content

    def _master_credito_txt(self):
        self.ensure_one()

        if not self.journal_id.direct_debit_merchant_number:
            raise UserError(
                'Debe completar el numero de comercio en el diario con nombre %s, id: %s' % (
                    self.journal_id.name, self.journal_id.id))

        if not self.periodo:
            raise UserError('Debe indicar el periodo con formato MM/AA')

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

        # importe
        content += ('%015.2f' % abs(self.amount)).replace('.','')

        # filler
        content += ' '*91

        content += '\n'

        for rec in self.payment_ids:
            # nro de comercio
            content += self.journal_id.direct_debit_merchant_number.ljust(8)
            # tipo de comercio
            content += '2'

            # nro tarjeta
            content += '%016d' % int(rec.direct_debit_mandate_id.credit_card_number)

            content += self._get_reference(rec, 12, onlydigits=True)

            # nro de cuota
            content += '001'

            # cuotas plan
            content += '999'

            # frecuencia db
            content += '01'

            # importe
            content += ('%012.2f' % abs(self.amount)).replace('.','')

            # periodo
            content += self.periodo

            # filler
            content += ' '*67

            content += '\n'

        return content

    def _visa_txt(self):
        self.ensure_one()
        if not self.journal_id.direct_debit_merchant_number or not self.direct_debit_collection_date:
            raise UserError(
                'Debe completar el numero de establecimiento (10 dígitos) en el diario con nombre %s, id: %s y '
                'también el campo Collection date que representa la fecha de vencimiento' % (
                    self.journal_id.name, self.journal_id.id))

        content = ''

        # ENCABEZADO
        # tipo de registro
        content += '0'
        if self.direct_debit_format == 'visa_debito':
            content += 'DEBLIQD '
        elif self.direct_debit_format == 'visa_credito':
            content += 'DEBLIQC '

        # nro de establecimiento
        nro_establecimiento = '%010d' % int(self.journal_id.direct_debit_merchant_number[:10])
        content += nro_establecimiento
        content += '900000    '

        # fecha de generación del archivo
        fecha_generacion = self.date.strftime("%Y%m%d")
        content += fecha_generacion

        # hora generación archivo
        current_datetime = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        hora = current_datetime.strftime("%H%M")
        content += hora

        # tipo de archivo. Débitos a liquidar
        content += '0'

        # estado archivo + reservado
        content += ' '*57

        # marca fin de registro
        content += '*'

        content += '\n'

        mandates_already_used = self.env['account.payment'].search([
            ('batch_payment_id.id', '!=', self.id),
            ('batch_payment_id.state', 'in', ['sent', 'reconciled']),
            ('direct_debit_mandate_id', 'in', self.mapped('payment_ids.direct_debit_mandate_id').ids),
            ]).mapped('direct_debit_mandate_id')

        for rec in self.payment_ids:
            # tipo de registro
            content += '1'

            # numero de tarjeta
            content += '%016d' % int(rec.direct_debit_mandate_id.credit_card_number)

            # reservado
            content += '   '

            # referencia
            content += self._get_reference(rec, 8, onlydigits=True)

            # fecha de origen o vencimiento del débito
            content += self.direct_debit_collection_date.strftime("%Y%m%d")

            # código de transacción
            content += '0005'

            # importe a debitar, ver si lleva o no separador de decimales, sigo la misma lógica de los otros txt
            content += ('%016.2f' % rec.amount).replace('.', '')

            # identificador del débito (lo tiene que consultar jjs con el cliente)
            content += '%05d' % int(rec.partner_id.ref)
            content += ' '*10

            # si es la primera vez que se debita con la tarjeta pasar "E", si no " "
            content += ' ' if rec.direct_debit_mandate_id in mandates_already_used else 'E'

            # espacios
            content += ' '*28

            # marca de fin *
            content += '*'
            content += '\n'

        # PIE
        # constante
        content += '9'
        if self.direct_debit_format == 'visa_debito':
            content += 'DEBLIQD '
        elif self.direct_debit_format == 'visa_credito':
            content += 'DEBLIQC '

        # nro de establecimiento
        content += nro_establecimiento
        content += '900000    '

        # fecha de generación del archivo
        content += fecha_generacion

        # hora generación archivo
        content += hora

        # cantidad de registros
        content += '%07d' % len(self.payment_ids)

        # sumatoria importes
        content += ('%016.2f' % self.amount).replace('.','')

        # estado archivo + reservado
        content += ' '*36

        # marca fin de registro
        content += '*'

        # caracter de control (1 enter)
        content += '\n'

        return content

    def _generate_export_file(self):
        if not self.direct_debit_format:
            return super()._generate_export_file()
        if self.direct_debit_format == 'cbu_galicia':
            content = self._galicia_debito_txt()
        elif self.direct_debit_format == 'cbu_macro':
            content = self._macro_cbu()
        elif self.direct_debit_format == 'master_credito':
            content = self._master_credito_txt()
        elif self.direct_debit_format == 'visa_credito' or self.direct_debit_format == 'visa_debito':
            content = self._visa_txt()
        return {
            'file': base64.encodebytes(content.encode('UTF-8')),
            'filename': "Archivo Débito Automático-" + self.journal_id.code + "-" + datetime.now().strftime('%Y%m%d%H%M%S') + ".txt",
        }

    def _get_methods_generating_files(self):
        rslt = super()._get_methods_generating_files()
        rslt.append('dd')
        return rslt

    def validate_batch(self):
        return super().validate_batch()
