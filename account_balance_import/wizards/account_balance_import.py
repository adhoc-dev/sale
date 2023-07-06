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
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )

    counterpart_account_id = fields.Many2one(
        "account.account",
        string="Cuenta de Contrapartida",
        default=lambda self: self.env.company.get_unaffected_earnings_account(),
        help="Recomendamos utilizar la misma cuenta de contrapartida "
        "para todos los asientos iniciales",
        domain="[('company_id','=', company_id), ('deprecated', '=', False)]",
    )

    mode = fields.Selection(
        [
            ("account_balance", _("Saldos Contables")),
            ("partner_balance", _("Saldos de Partners")),
            ("check_balance", _("Cheques")),
        ],
        string="Modo de Importación",
        required=True,
        default="account_balance",
    )
    accounting_date = fields.Date("Fecha Contable", required=True)

    # Account Balance Related Fields
    account_opening_entries_journal_id = fields.Many2one(
        "account.journal",
        string="Diario de Asientos de Apertura",
        domain="[('company_id', '=', company_id)," "('type', '=', 'general')]",
    )

    account_balance_file = fields.Binary("Archivo de Importación de Saldos Contables")

    # Company Balance Related Fields
    partner_balance_journal_id = fields.Many2one(
        "account.journal",
        string=_("Diario"),
        domain="[('company_id', '=', company_id)," "('type', '=', 'general')]",
    )

    partner_balance_type = fields.Selection(
        [("receivable", "Por Cobrar"), ("payable", "A Pagar")],
        "Tipo de Saldo",
        default="receivable",
    )

    partner_balance_file = fields.Binary("Archivo de Importación de Saldos de Partners")

    # Check Related Fields
    check_type = fields.Selection(
        [("issue_check", "Propios"), ("third_check", "De Terceros")],
        string="Tipo de Cheques",
        default="issue_check",
    )

    check_journal_bank_id = fields.Many2one(
        "account.journal",
        string="Diario de Banco",
        domain="[('company_id', '=', company_id)," "('type', '=', 'bank'),"
       "('outbound_payment_method_line_ids.code', '=', 'check_printing')]"
    )

    check_journal_third_id = fields.Many2one(
        "account.journal",
        string="Diario de Cheques de Terceros",
        domain="[('company_id', '=', company_id)," "('type', '=', 'cash'),"
       "('inbound_payment_method_line_ids.code', '=', 'in_third_party_checks')]"
    )

    check_file = fields.Binary("Archivo de Importación de Cheques")

    def action_generate_xls(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": "/account_balance_import/generate_xls/" + str(self.company_id.id),
            "target": "new",
        }

    @api.model
    def locate_currency(self, currency):
        """This method return the currency, if wasn't find any currency that match with the name in xls we return empty recordset"""
        other_currency = self.env["res.currency"]
        if currency:
            other_currency = self.env["res.currency"]._search_by_name(currency)
        return other_currency

    def account_balance_import_xls(self):
        """Triggered on when Account Balance XLS is imported
        This function will firstly read the entire XLS file and perform
        checks on each one of the rows to make sure the import looks good.
        If everything goes fine, the account moves are created and displayed.
        If any error is found, a message with the offending lines and their
        description is presented.
        """

        # Set-up environment company
        if not self.account_balance_file:
            raise ValidationError(
                'Debe subir el archivo "Archivo de Importación de Saldos Contables"'
            )
        self = self.with_company(self.company_id.id)

        fields = [
            "code",
            "name",
            "amount",
            "reference",
            "currency",
            "amount_company_currency",
        ]

        errors = list()  # For storing possible errors
        move_lines = list()  # For storing items before generating 'em

        company = self.company_id
        journal = self.account_opening_entries_journal_id

        # Parse XLS file
        decoded = base64.decodebytes(self.account_balance_file)
        workbook = xlrd.open_workbook(file_contents=decoded)
        sheet = workbook.sheet_by_index(0)

        # Iterate over each sheet row
        for row_no in range(1, sheet.nrows):
            # Create a dict with current row data
            dict_data = {
                fields[i]: sheet.row(row_no)[i].value for i in range(0, len(fields))
            }

            if dict_data["amount"] == "":
                # No amount was provided for this line, skip silently
                continue

            # Locate Account
            account = self.env["account.account"].search(
                [
                    ("company_id", "=", company.id),
                    ("code", "=", dict_data["code"]),
                ]
            )

            # Locate Currency
            other_currency = self.locate_currency(dict_data["currency"])

            if other_currency and not dict_data["amount_company_currency"]:
                errors.append(
                    "Fila {}: Si le establece otra moneda debe indicar el importe en esa otra moneda".format(
                        str(row_no + 1)
                    )
                )
                continue

            if other_currency and other_currency != account.currency_id:
                errors.append(
                    'La moneda elegida "{}" en el movimiento para la cuenta "{}" no coincide con la de la cuenta "{}".'
                    "\n ¡Deberia cambiar la moneda en el movimiento!.".format(
                        dict_data["currency"],
                        account.display_name,
                        account.currency_id.name,
                    )
                )
                continue

            # Skip if account was not found
            if not account:
                errors.append(
                    "Fila {}: No se encontró ninguna cuenta para el "
                    "texto ingresado ({}).".format(str(row_no + 1), dict_data["name"])
                )
                continue
            elif account.deprecated:
                errors.append(
                    "Fila {}: La cuenta '{}' ({}) se encuentra depreciada y "
                    "no puede utilizarse.".format(
                        str(row_no + 1), account.name, account.code
                    )
                )
                continue

            # Skip if amount isn't numerical
            if not isinstance(dict_data["amount"], numbers.Number):
                errors.append(
                    "Fila {}: El monto ingresado no es númerico.".format(
                        str(row_no + 1)
                    )
                )
                continue

            if dict_data["amount"] > 0:
                debit = self.company_id.currency_id.round(dict_data["amount"])
                credit = 0.0
                # counterpart_credit_move_line["credit"] += debit
            elif dict_data["amount"] < 0:
                debit = 0.0
                credit = abs(self.company_id.currency_id.round(dict_data["amount"]))
                # counterpart_debit_move_line["debit"] += credit
            else:
                # Skip element if amount == 0
                continue

            amount_company_currency = (
                other_currency
                and other_currency.round(dict_data["amount_company_currency"])
                or False
            )

            line = {
                "name": dict_data.get("reference", None) or _("Opening balance"),
                "account_id": account.id,
                "company_id": self.company_id.id,
                "debit": debit,
                "credit": credit,
            }
            if other_currency:
                line.update(
                    {
                        "currency_id": other_currency.id,
                        "amount_currency": (-1.0 if line["debit"] == 0.0 else 1.0)
                        * amount_company_currency,
                    }
                )

            move_lines.append(line)

        # Check if there were errors when iterating over XLS rows
        if len(errors) > 0:
            raise ValidationError("\n".join(errors))

        if len(move_lines) == 0:
            raise ValidationError("El archivo importado no contiene movimientos.")

        debits_sum = credits_sum = 0.0
        for line in move_lines:
            debits_sum += line["debit"]
            credits_sum += line["credit"]

        # Code taken from method opening_move_line_ids_changed
        currency = self.company_id.currency_id
        difference = abs(debits_sum - credits_sum)
        debit_diff = (
            (debits_sum > credits_sum)
            and float_round(difference, precision_rounding=currency.rounding)
            or 0.0
        )
        credit_diff = (
            (debits_sum < credits_sum)
            and float_round(difference, precision_rounding=currency.rounding)
            or 0.0
        )

        if debit_diff or credit_diff:
            move_lines.append(
                {
                    "name": _("Automatic Balancing Line"),
                    "account_id": self.counterpart_account_id.id,
                    "debit": credit_diff,
                    "credit": debit_diff,
                    "company_id": self.company_id.id,
                }
            )

        # Create account move and lines
        account_move = self.env["account.move"].create(
            {
                "journal_id": journal.id,
                "date": self.accounting_date,
                "line_ids": [(0, 0, item) for item in move_lines],
            }
        )

        # Post movement
        account_move._post()

        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "account.move",
            "res_id": account_move.id,
            "views": [(False, "form")],
            "target": "current",
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
        self = self.with_company(self.company_id.id)

        fields = [
            "name",
            "reference",
            "amount",
            "due_date",
            "currency",
            "amount_company_currency",
        ]

        account_moves = list()  # For storing account moves before creating 'em
        errors = list()  # For storing possible errors
        company = self.env.company
        journal = self.partner_balance_journal_id

        # Parse XLS file
        decoded = base64.decodebytes(self.partner_balance_file)
        workbook = xlrd.open_workbook(file_contents=decoded)
        sheet = workbook.sheet_by_index(0)

        # Iterate over each sheet row
        for row_no in range(1, sheet.nrows):

            # Create a dict with current row data
            dict_data = {
                fields[i]: sheet.row(row_no)[i].value for i in range(0, len(fields))
            }

            # Parse name as string to prevent CUIT being read as float
            if isinstance(dict_data["name"], numbers.Number):
                dict_data["name"] = str(int(dict_data["name"]))

            # Locate Partner
            domain = [
                "|",
                "|",
                ("name", "=", dict_data["name"]),
                ("vat", "=", dict_data["name"]),
                ("ref", "=", dict_data["name"]),
            ]

            partner = self.env["res.partner"].search(domain)

            # Locate Currency
            other_currency = self.locate_currency(dict_data["currency"])

            if other_currency and not dict_data["amount_company_currency"]:
                errors.append(
                    "Fila {}: Si le establece otra moneda debe indicar el importe en esa otra moneda".format(
                        str(row_no + 1)
                    )
                )
                continue

            # Skip if partner not found
            if not partner:
                errors.append(
                    "Fila {}: No se encontró ningún partner "
                    "para el texto ingresado ({}).".format(
                        str(row_no + 1), dict_data["name"]
                    )
                )
                continue

            # Skip if more than one parter was found
            if len(partner) > 1:
                errors.append(
                    "Fila {}: Se encontraron varios partners "
                    "para el texto ingresado ({}). ¡Revise los datos Cargados!".format(
                        str(row_no + 1), dict_data["name"]
                    )
                )
                continue

            # Skip if amount isn't numerical
            if not isinstance(dict_data["amount"], numbers.Number):
                errors.append(
                    "Fila {}: El monto no es numérico.".format(str(row_no + 1))
                )
                continue

            if dict_data["due_date"] != "":
                try:
                    due_date = datetime.datetime(
                        *xlrd.xldate_as_tuple(dict_data["due_date"], workbook.datemode)
                    ).date()
                except TypeError:
                    # Skip if we're not able to parse due_date
                    errors.append(
                        "Fila {}: Formato de fecha de vencimiento desconocido. "
                        "Asegúrese de que la columna posee "
                        "formato de fecha.".format(str(row_no + 1))
                    )
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
                    continue  # Skip silently if amount is 0
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
                    continue  # Skip silently if amount is 0

            # Skip if partner account account is obsolete
            if partner_account.deprecated:
                errors.append(
                    "Fila {}: La cuenta asociada al partner {} "
                    "se encuentra depreciada.".format(str(row_no + 1), partner.name)
                )
                continue

            # Check if accounts have the same company.
            if company.id != partner_account.company_id.id:
                errors.append(
                    "Fila {}: Una de las cuentas asociadas al "
                    "partner {} no pertenece a la compañía ({})".format(
                        str(row_no + 1), partner.name, company.name
                    )
                )
                continue

            amount_company_currency = (
                other_currency
                and other_currency.round(dict_data["amount_company_currency"])
                or False
            )

            # Create move lines
            line_1 = {
                "name": dict_data["reference"],
                "partner_id": partner.id,
                "account_id": partner_account.id,
                "debit": debit,
                "credit": credit,
                "date_maturity": due_date,
            }

            line_2 = {
                "name": dict_data["reference"],
                "partner_id": partner.id,
                "account_id": self.counterpart_account_id.id,
                "debit": credit,
                "credit": debit,
                "date_maturity": due_date,
            }
            if other_currency:
                line_1.update(
                    {
                        "currency_id": other_currency.id,
                        "amount_currency": (-1.0 if line_1["debit"] == 0.0 else 1.0)
                        * amount_company_currency,
                    }
                )
                line_2.update(
                    {
                        "currency_id": other_currency.id,
                        "amount_currency": (1.0 if line_2["credit"] == 0.0 else -1.0)
                        * amount_company_currency,
                    }
                )
            # Add account move to list
            account_moves.append(
                {
                    "journal_id": journal.id,
                    "ref": dict_data["reference"],
                    "date": self.accounting_date,
                    "line_ids": [
                        (0, 0, line_1),
                        (0, 0, line_2),
                    ],
                }
            )

        # Check if there were errors when iterating over XLS rows
        if len(errors) > 0:
            raise ValidationError("\n".join(errors))

        # Everything should be OK if we reached this part
        generated_moves = self.env["account.move"].create(account_moves)
        # Post Account Move
        generated_moves._post()

        return {
            "name": "Importación de Saldos Iniciales",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "account.move",
            "views": [(False, "tree"), (False, "form")],
            "target": "current",
            "domain": [("id", "in", generated_moves.ids)],
        }

    def check_balance_import_xls(self):
        """Triggered on when Checks XLS is imported"""

        # Set-up environment company
        self = self.with_company(self.company_id.id)

        fields = [
            "number",
            "amount",
            "payment_date",
            "name",
            "currency",
            "amount_company_currency",
        ]
        if self.check_type == "third_check":
            fields.insert(4,"owner_vat")

        generated_move_ids = list()  # For storing generated account move ids
        pre_data = list()  # For storing data before persisting to db
        errors = list()  # For storing possible errors

        # Parse XLS file
        decoded = base64.decodebytes(self.check_file)
        workbook = xlrd.open_workbook(file_contents=decoded)
        sheet = workbook.sheet_by_index(0)

        # Get Journal
        if self.check_type == "issue_check":
            journal = self.check_journal_bank_id
            payment_method_line = self.check_journal_bank_id._get_available_payment_method_lines('outbound').filtered(lambda x: x.code == 'check_printing')
        else:  # Third-party Check
            journal = self.check_journal_third_id
            payment_method_line = self.check_journal_third_id._get_available_payment_method_lines('inbound').filtered(lambda x: x.code == 'new_third_party_checks')

        # Iterate over each sheet row
        for row_no in range(1, sheet.nrows):

            # Create a dict with current row data
            dict_data = {
                fields[i]: sheet.row(row_no)[i].value for i in range(0, len(fields))
            }

            # Parse name as string to prevent CUIT being read as float
            if isinstance(dict_data["name"], numbers.Number):
                dict_data["name"] = str(int(dict_data["name"]))

            # Locate Partner
            domain = [
                "|",
                "|",
                ("name", "=", dict_data["name"]),
                ("vat", "=", dict_data["name"]),
                ("ref", "=", dict_data["name"]),
            ]

            partner = self.env["res.partner"].search(domain)

            # Locate Currency
            other_currency = self.locate_currency(dict_data["currency"])

            if other_currency and not dict_data["amount_company_currency"]:
                errors.append(
                    "Fila {}: Si le establece otra moneda debe indicar el importe en esa otra moneda".format(
                        str(row_no + 1)
                    )
                )
                continue

            # Skip if partner not found
            if not partner:
                errors.append(
                    "Fila {}: No se encontró ningún partner "
                    "para el texto ingresado ({})".format(
                        str(row_no + 1), dict_data["name"]
                    )
                )
                continue

            partner = partner.mapped("commercial_partner_id")
            # Skip if more than one parter was found
            if len(partner) > 1:
                errors.append(
                    "Fila {}: Se encontraron varios partners "
                    "para el texto ingresado ({}). ¡Revise los datos Cargados!".format(
                        str(row_no + 1), dict_data['name']))
                continue

            # Skip if we're not able to parse due_date
            try:
                payment_date = datetime.datetime(
                    *xlrd.xldate_as_tuple(dict_data["payment_date"], workbook.datemode)
                ).date()
            except TypeError:
                errors.append(
                    "Fila {}: Formato de fecha de pago desconocido. "
                    "Asegúrese de que la columna posee "
                    "formato de fecha.".format(str(row_no + 1))
                )
                continue

            try:
                number = str(int(dict_data["number"]))
            except ValueError:
                errors.append(
                    "Fila {}: Número de cheque inválido. ".format(str(row_no + 1))
                )
                continue

            amount = self.company_id.currency_id.round(dict_data["amount"])
            amount_company_currency = (
                other_currency
                and other_currency.round(dict_data["amount_company_currency"])
                or False
            )

            check_data = {
                "partner_id": partner.id,
                "check_number": number,
                "amount": dict_data["amount"],
                "l10n_latam_check_bank_id": journal.bank_id.id,
                "name": "Saldo Inicial - Cheque Nº. {}".format(number),
                "journal_id": journal.id,
                "payment_type": 'inbound',
                "l10n_latam_check_payment_date": payment_date,
                "date": self.accounting_date,
                "payment_method_line_id": payment_method_line.id,
            }
            if self.check_type == "issue_check":
                check_data.update({
                    "payment_type": 'outbound',
                    })

            if other_currency and amount_company_currency:
                check_data.update(
                    {
                        "amount": amount_company_currency,
                        "amount_company_currency": dict_data["amount"],
                        "currency_id": other_currency.id,
                    }
                )

            pre_data.append((check_data, partner.id))

        # Check if there were errors when iterating over XLS rows
        if len(errors) > 0:
            raise ValidationError("\n".join(errors))

        if len(pre_data) == 0:
            raise ValidationError("El archivo importado no contiene movimientos.")
        payments = self.env['account.payment']
        for check_data, partid in pre_data:
            payment = self.env["account.payment"].create(check_data)
            payment.write({'check_number': check_data["check_number"]})
            payments += payment
        payments.action_post()
        for payment in payments.with_context(skip_account_move_synchronization=True):
            payment.move_id.line_ids.filtered(
                lambda x: x.account_id.account_type in ('asset_receivable', 'liability_payable')).account_id = self.counterpart_account_id

        return {
            "name": "Importación de Saldos Iniciales",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "account.payment",
            "views": [(False, "tree"), (False, "form")],
            "target": "current",
            "domain": [("id", "in", payments.ids)],
        }
