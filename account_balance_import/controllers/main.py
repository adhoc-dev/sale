import io
import xlwt
import base64
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import content_disposition


class GenerateXLS(http.Controller):
    @http.route('/account_balance_import/generate_xls/<int:company_id>/', type='http')
    def generate_account_balance_xls(self, company_id):
        """ Generate a XLS file with that contains the existing
        non-payable and non-receivable accounts, so the user can
        fill it in.
        """
        # Fetch accounts
        accounts = request.env["account.account"].search([
            ("account_type", "not in", ["receivable", "payable"]),
            ("company_id", "=", company_id)
        ]).sorted().read(["code", "name"])
        # Create workbook
        workbook = xlwt.Workbook(encoding='utf8')
        # Create style for headers row
        style = xlwt.easyxf('pattern: pattern solid, fore_colour light_yellow')
        # Create a new sheet
        sheet = workbook.add_sheet('Account Balance Import')
        # Adjust column width, each character is about 256 units wide
        sheet.col(0).width = 256 * 20
        sheet.col(1).width = 256 * 40
        sheet.col(2).width = 256 * 40
        sheet.col(3).width = 256 * 40
        sheet.col(4).width = 256 * 20
        sheet.col(5).width = 256 * 30
        # Write titles
        sheet.write(0, 0, "Código (No Editar)", style)
        sheet.write(0, 1, "Nombre (No Editar)", style)
        sheet.write(0, 2, "Saldo (Positivo o Negativo)", style)
        sheet.write(0, 3, "Referencia", style)
        sheet.write(0, 4, "Otra Moneda (Opcional)", style)
        sheet.write(0, 5, "Importe en Otra moneda (Opcional)", style)
        # Fill code and name columns
        for idx, account in enumerate(accounts):
            sheet.write(idx + 1, 0, account["code"])
            sheet.write(idx + 1, 1, account["name"])
        # Create a bytes stream
        f = io.BytesIO()
        # Save workbook to stream
        workbook.save(f)
        f.seek(0)
        # Return stream as a file download
        return request.make_response(
            f.getvalue(),
            [('Content-Type', 'application/octet-stream'),
             ('Content-Disposition', content_disposition(
                 "account_balance.xls"))])
