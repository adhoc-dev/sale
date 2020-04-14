from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round
import xlrd
import base64
import numbers
import logging
import datetime

_logger = logging.getLogger(__name__)


class AccountBalanceImport(models.TransientModel):
    _name = "account_balance_import"
    _description = "Account Initial Balance Wizard"

    # Common Fields
    company_id = fields.Many2one(
        'res.company', string='Compañía',
        required=True,
        default=lambda self: self.env.user.company_id)

    counterpart_account_id = fields.Many2one(
        "account.account", string="Cuenta de Contrapartida",
        default=lambda
        self: self.env.user.company_id.get_unaffected_earnings_account(),
        help="Recomendamos utilizar la misma cuenta de contrapartida "
        "para todos los asientos iniciales",
        domain="[('company_id','=', company_id), ('deprecated', '=', False)]")

    mode = fields.Selection(
        [
            ("account_balance", _("Saldos Contables")),
            ("partner_balance", _("Saldos de Partners")),
            ("check_balance", _("Cheques")),
        ],
        string="Modo de Importación",
        required=True,
        default="account_balance"
    )
    accounting_date = fields.Date("Fecha Contable", required=True)

    # Account Balance Related Fields
    account_opening_entries_journal_id = fields.Many2one(
        "account.journal", string="Diario de Asientos de Apertura",
        domain="[('company_id', '=', company_id),"
               "('type', '=', 'general')]")

    account_balance_file = fields.Binary(
        "Archivo de Importación de Saldos Contables")

    # Company Balance Related Fields
    partner_balance_journal_id = fields.Many2one(
        "account.journal", string=_("Diario"),
        domain="[('company_id', '=', company_id),"
               "('type', '=', 'general')]")

    partner_balance_type = fields.Selection(
        [("receivable", "Por Cobrar"),
         ("payable", "A Pagar")],
        "Tipo de Saldo",
        default="receivable"
    )

    partner_balance_file = fields.Binary(
        "Archivo de Importación de Saldos de Partners")

    # Check Related Fields
    check_type = fields.Selection(
        [("issue_check", "Propios"),
         ("third_check", "De Terceros")],
        string="Tipo de Cheques",
        default="issue_check"
    )

    check_journal_bank_id = fields.Many2one(
        "account.journal",
        string="Diario de Banco",
        domain="[('company_id', '=', company_id),"
               "('type', '=', 'bank'),"
               "('outbound_payment_method_ids.code', '=', 'issue_check')]")

    check_journal_third_id = fields.Many2one(
        "account.journal", string="Diario de Cheques de Terceros",
        domain="[('company_id', '=', company_id),"
               "('inbound_payment_method_ids.code', '=', 'received_third_check')]")

    check_checkbook_id = fields.Many2one(
        "account.checkbook", string="Chequera")

    check_file = fields.Binary("Archivo de Importación de Cheques")

    def account_balance_import_xls(self):
        """ Triggered on when Account Balance XLS is imported
        This function will firstly read the entire XLS file and perform
        checks on each one of the rows to make sure the import looks good.
        If everything goes fine, the account moves are created and displayed.
        If any error is found, a message with the offending lines and their
        description is presented.
        """

        # Set-up environment company
        self = self.with_context(force_company=self.company_id.id)

        fields = [
            "code",
            "name",
            "amount",
            "reference"
        ]

        errors = list()         # For storing possible errors
        move_lines = list()     # For storing items before generating 'em

        company = self.company_id
        journal = self.account_opening_entries_journal_id

        # Parse XLS file
        decoded = base64.decodestring(self.account_balance_file)
        workbook = xlrd.open_workbook(file_contents=decoded)
        sheet = workbook.sheet_by_index(0)

        # Iterate over each sheet row
        for row_no in range(1, sheet.nrows):
            # Create a dict with current row data
            dict_data = {
                fields[i]: sheet.row(row_no)[i].value
                for i in range(0, len(fields))}

            if dict_data["amount"] == "":
                # No amount was provided for this line, skip silently
                continue

            # Locate Account
            account = self.env["account.account"].search([
                ("company_id", "=", company.id),
                ("code", "=", dict_data["code"]),
            ])

            # Skip if account was not found
            if not account:
                errors.append(
                    "Fila {}: No se encontró ninguna cuenta para el "
                    "texto ingresado ({}).".format(
                        str(row_no + 1), dict_data['name']))
                continue
            elif account.deprecated:
                errors.append(
                    "Fila {}: La cuenta '{}' ({}) se encuentra depreciada y "
                    "no puede utilizarse.".format(
                        str(row_no + 1), account.name, account.code))
                continue

            # Skip if amount isn't numerical
            if not isinstance(dict_data['amount'], numbers.Number):
                errors.append(
                    "Fila {}: El monto ingresado no es númerico.".format(
                        str(row_no + 1)))
                continue

            if dict_data['amount'] > 0:
                debit = self.company_id.currency_id.round(dict_data['amount'])
                credit = 0.0
                # counterpart_credit_move_line["credit"] += debit
            elif dict_data['amount'] < 0:
                debit = 0.0
                credit = abs(self.company_id.currency_id.round(
                    dict_data['amount']))
                # counterpart_debit_move_line["debit"] += credit
            else:
                # Skip element if amount == 0
                continue

            line = {
                "name": dict_data.get("reference", None) or
                _("Opening balance"),
                "account_id": account.id,
                'company_id': self.company_id.id,
                "debit": debit,
                "credit": credit
                }

            move_lines.append(line)

        # Check if there were errors when iterating over XLS rows
        if len(errors) > 0:
            raise ValidationError("\n".join(errors))

        if len(move_lines) == 0:
            raise ValidationError(
                "El archivo importado no contiene movimientos.")

        debits_sum = credits_sum = 0.0
        for line in move_lines:
            debits_sum += line["debit"]
            credits_sum += line["credit"]

        # Code taken from method opening_move_line_ids_changed
        currency = self.company_id.currency_id
        difference = abs(debits_sum - credits_sum)
        debit_diff = (debits_sum > credits_sum) and float_round(
            difference, precision_rounding=currency.rounding) or 0.0
        credit_diff = (debits_sum < credits_sum) and float_round(
            difference, precision_rounding=currency.rounding) or 0.0

        if debit_diff or credit_diff:
            move_lines.append({
                'name': _('Automatic Balancing Line'),
                'account_id': self.counterpart_account_id.id,
                'debit': credit_diff,
                'credit': debit_diff,
                'company_id': self.company_id.id,
            })

        # Create account move and lines
        account_move = self.env['account.move'].create(
            {"journal_id": journal.id,
             "date": self.accounting_date,
             "line_ids": [(0, 0, item) for item in move_lines]})

        # Post movement
        account_move.post()

        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "account.move",
            "res_id": account_move.id,
            "views": [(False, "form")],
            "target": "current"
        }

    def partner_balance_import_xls(self):
        """Triggered on when Company Balance XLS is imported
        This function will firstly read the entire XLS file and perform
        checks on each one of the rows to make sure the import looks good.
        If everything goes fine, the account moves are created and displayed.
        If any error is found, a message with the offending lines and their
        description is presented.
        """

        # Set-up environment company
        self = self.with_context(force_company=self.company_id.id)

        fields = [
            "name",
            "reference",
            "amount",
            "date",
            "due_date"
        ]

        account_moves = list()  # For storing account moves before creating 'em
        errors = list()         # For storing possible errors
        generated_move_ids = list()  # Used for storing ids of generated items
        company = self.env.user.company_id
        journal = self.partner_balance_journal_id

        # Parse XLS file
        decoded = base64.decodestring(self.partner_balance_file)
        workbook = xlrd.open_workbook(file_contents=decoded)
        sheet = workbook.sheet_by_index(0)

        # Iterate over each sheet row
        for row_no in range(1, sheet.nrows):

            # Create a dict with current row data
            dict_data = {
                fields[i]: sheet.row(row_no)[i].value
                for i in range(0, len(fields))}

            # Parse name as string to prevent CUIT being read as float
            if isinstance(dict_data["name"], numbers.Number):
                dict_data["name"] = str(int(dict_data["name"]))

            # Locate Partner
            domain = [
                "|", "|",
                ("name", "=", dict_data["name"]),
                ("main_id_number", "=", dict_data["name"]),
                ("ref", "=", dict_data["name"])
            ]

            partner = self.env["res.partner"].search(domain)

            # Skip if partner not found
            if not partner:
                errors.append(
                    "Fila {}: No se encontró ningún partner "
                    "para el texto ingresado ({}).".format(
                        str(row_no + 1), dict_data['name']))
                continue

            # Skip if amount isn't numerical
            if not isinstance(dict_data['amount'], numbers.Number):
                errors.append(
                    "Fila {}: El monto no es numérico.".format(
                        str(row_no + 1)))
                continue

            if dict_data["date"] != "":
                try:
                    accounting_date = datetime.datetime(
                        *xlrd.xldate_as_tuple(
                            dict_data["date"],
                            workbook.datemode)).date()
                except TypeError:
                    # Skip if we're not able to parse date
                    errors.append(
                        "Fila {}: Formato de fecha desconocido. "
                        "Asegúrese de que la columna posee "
                        "formato de fecha.".format(
                            str(row_no + 1)))
                    continue
            else:
                # Default to accounting date if omitted
                accounting_date = self.accounting_date

            if dict_data["due_date"] != "":
                try:
                    due_date = datetime.datetime(
                        *xlrd.xldate_as_tuple(
                            dict_data["due_date"],
                            workbook.datemode)).date()
                except TypeError:
                    # Skip if we're not able to parse due_date
                    errors.append(
                        "Fila {}: Formato de fecha de vencimiento desconocido. "
                        "Asegúrese de que la columna posee "
                        "formato de fecha.".format(
                            str(row_no + 1)))
                    continue
            else:
                # Default to blank if ommited
                due_date = False

            # Get account depending on selected type
            if self.partner_balance_type == "receivable":
                # Receivable
                partner_account = partner.property_account_receivable_id
                if dict_data["amount"] > 0:
                    debit = self.company_id.currency_id.round(dict_data["amount"])
                    credit = 0.0
                elif dict_data["amount"] < 0:
                    debit = 0.0
                    credit = self.company_id.currency_id.round(abs(dict_data["amount"]))
                else:
                    continue    # Skip silently if amount is 0
            else:
                # Payable
                partner_account = partner.property_account_payable_id
                if dict_data["amount"] > 0:
                    debit = 0.0
                    credit = self.company_id.currency_id.round(dict_data["amount"])
                elif dict_data["amount"] < 0:
                    debit = self.company_id.currency_id.round(abs(dict_data["amount"]))
                    credit = 0.0
                else:
                    continue    # Skip silently if amount is 0

            # Skip if partner account account is obsolete
            if partner_account.deprecated:
                errors.append(
                    "Fila {}: La cuenta asociada al partner {} "
                    "se encuentra depreciada.".format(
                        str(row_no + 1), partner.name))
                continue

            # Check if accounts have the same company.
            if (company.id != partner_account.company_id.id):
                errors.append(
                    "Fila {}: Una de las cuentas asociadas al "
                    "partner {} no pertenece a la compañía ({})".format(
                        str(row_no + 1),
                        partner.name, company.name))
                continue

            # Create move lines
            line_1 = {
                "name": dict_data["reference"],
                "partner_id": partner.id,
                "account_id": partner_account.id,
                "debit": debit,
                "credit": credit,
                "date": accounting_date,
                "date_maturity": due_date
            }

            line_2 = {
                "name": dict_data["reference"],
                "partner_id": partner.id,
                "account_id": self.counterpart_account_id.id,
                "debit": credit,
                "credit": debit,
                "date": accounting_date,
                "date_maturity": due_date
            }

            # Add account move to list
            account_moves.append({
                "journal_id": journal.id,
                "ref": dict_data["reference"],
                "date": self.accounting_date,
                "line_ids": [
                    (0, 0, line_1),
                    (0, 0, line_2),
                ]
            })

        # Check if there were errors when iterating over XLS rows
        if len(errors) > 0:
            raise ValidationError("\n".join(errors))

        # Everything should be OK if we reached this part
        # TODO: Optimizar, usar create multi
        for item in account_moves:
            account_move = self.env['account.move'].create(item)
            # Post Account Move
            account_move.post()
            # Append generated move id
            generated_move_ids.append(account_move.id)

        return {
            "name": "Importación de Saldos Iniciales",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "account.move",
            "views": [(False, "tree"), (False, "form")],
            "target": "current",
            "domain": [("id", "in", generated_move_ids)]
        }

    def check_balance_import_xls(self):
        """ Triggered on when Checks XLS is imported
        """

        # Set-up environment company
        self = self.with_context(force_company=self.company_id.id)

        fields = [
            "number",
            "amount",
            "issue_date",
            "payment_date",
            "name",
            "owner_name",
            "owner_vat"
        ]

        generated_move_ids = list()   # For storing generated account move ids
        pre_data = list()        # For storing data before persisting to db
        errors = list()         # For storing possible errors

        # Parse XLS file
        decoded = base64.decodestring(self.check_file)
        workbook = xlrd.open_workbook(file_contents=decoded)
        sheet = workbook.sheet_by_index(0)

        # Get Journal
        if self.check_type == 'issue_check':
            operation = "handed"
            journal = self.check_journal_bank_id
            account = self.company_id._get_check_account('deferred')
        else:  # Third-party Check
            operation = "holding"
            journal = self.check_journal_third_id
            account = journal.default_debit_account_id

        # Iterate over each sheet row
        for row_no in range(1, sheet.nrows):

            # Create a dict with current row data
            dict_data = {
                fields[i]: sheet.row(row_no)[i].value
                for i in range(0, len(fields))}

            # Parse name as string to prevent CUIT being read as float
            if isinstance(dict_data["name"], numbers.Number):
                dict_data["name"] = str(int(dict_data["name"]))

            # Locate Partner
            domain = [
                "|", "|",
                ("name", "=", dict_data["name"]),
                ("main_id_number", "=", dict_data["name"]),
                ("ref", "=", dict_data["name"])
            ]

            partner = self.env["res.partner"].search(domain)

            # Skip if partner not found
            if not partner:
                errors.append(
                    "Fila {}: No se encontró ningún partner "
                    "para el texto ingresado ({})".format(
                        str(row_no + 1), dict_data['name']))
                continue

            # Skip if we're not able to parse date
            try:
                issue_date = datetime.datetime(
                    *xlrd.xldate_as_tuple(
                        dict_data["issue_date"],
                        workbook.datemode)).date()
            except TypeError:
                errors.append(
                    "Fila {}: Formato de fecha de emisión desconocido. "
                    "Asegúrese de que la columna posee "
                    "formato de fecha.".format(
                        str(row_no + 1)))
                continue

            # Skip if we're not able to parse due_date
            try:
                payment_date = datetime.datetime(
                    *xlrd.xldate_as_tuple(
                        dict_data["payment_date"],
                        workbook.datemode)).date()
            except TypeError:
                errors.append(
                    "Fila {}: Formato de fecha de pago desconocido. "
                    "Asegúrese de que la columna posee "
                    "formato de fecha.".format(
                        str(row_no + 1)))
                continue

            try:
                number = str(int(dict_data["number"]))
            except ValueError:
                errors.append(
                    "Fila {}: Número de cheque inválido. ".format(
                        str(row_no + 1)))
                continue

            account_move_line_1 = {
                "name": "Cheque N°. {}".format(number),
                "account_id": account.id,
                "debit": self.company_id.currency_id.round(dict_data["amount"]),
                "credit": 0.0,
                "partner_id": partner.id
            }

            account_move_line_2 = {
                "name": "Cheque N°. {}".format(number),
                "account_id": self.counterpart_account_id.id,
                "debit": 0.0,
                "credit": self.company_id.currency_id.round(dict_data["amount"]),
                "partner_id": partner.id
            }

            move_data = {
                "date": self.accounting_date,
                "journal_id": journal.id,
                "ref": "Cheque N°. {}".format(number),
                "line_ids": [
                    (0, 0, account_move_line_1),
                    (0, 0, account_move_line_2)
                ]
            }

            check_data = {
                "number": number,
                "amount": dict_data["amount"],
                "bank_id": journal.bank_id.id,
                "type": self.check_type,
                "name": "Saldo Inicial - Cheque Nº. {}".format(number),
                "journal_id": journal.id,
                "checkbook_id": self.check_checkbook_id.id,
                "issue_date": issue_date,
                "payment_date": payment_date,
                "owner_name": dict_data["owner_name"],
                "owner_vat": str(int(dict_data["owner_vat"])) if dict_data["owner_vat"] else None,
            }

            pre_data.append((move_data, check_data, partner.id))

        # Check if there were errors when iterating over XLS rows
        if len(errors) > 0:
            raise ValidationError("\n".join(errors))

        if len(pre_data) == 0:
            raise ValidationError(
                "El archivo importado no contiene movimientos.")

        for move_data, check_data, partid in pre_data:
            # Create and Post Account Move
            account_move = self.env["account.move"].create(move_data)
            account_move.post()
            generated_move_ids.append(account_move.id)

            # Update check data, add move as operation
            check_data["operation_ids"] = [
                (0, 0, {
                    "date": self.accounting_date,
                    "operation": operation,
                    "origin": "{},{}".format("account.move", account_move.id),
                    "partner_id": partid
                })
            ]

            # Create Check
            self.env['account.check'].create(check_data)

        return {
            "name": "Importación de Saldos Iniciales",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "account.move",
            "views": [(False, "tree"), (False, "form")],
            "target": "current",
            "domain": [("id", "in", generated_move_ids)]
        }
