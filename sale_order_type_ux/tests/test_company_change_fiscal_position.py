# Copyright 2026 ADHOC SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCompanyChangeFiscalPosition(AccountTestInvoicingCommon):
    """The order type's fiscal position, and what happens when the company changes.

    On a sale order the company is an ordinary editable field, so it changes without the
    pencil that invoices get from ``account_multicompany_ux``. Either way it is a plain
    write, and a write recomputes the fiscal position but never the taxes of the lines:
    that is what the "Update Taxes" button next to the position is for, and nobody should
    have to press it after changing the company. In Argentina what was missing were the
    withholdings.

    And the override that makes the order type's position win used to take it whatever the
    company and without iterating, so an order moved elsewhere kept the position of the
    previous company — a value the field's own ``check_company`` does not accept, which
    reads as "it did not recompute".
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.company_data["company"]
        cls.company_b = cls.setup_other_company()["company"]
        # The accountman of the common fixture only carries its own company, and no rights
        # over sale orders or over the order types. All of it is fixture plumbing, not
        # what is being tested.
        cls.env.user.company_ids |= cls.company_a + cls.company_b
        cls.env.user.group_ids |= cls.env.ref("sales_team.group_sale_salesman")
        cls.customer = cls.env["res.partner"].create({"name": "Cliente"})

        cls.tax_a = cls.env["account.tax"].create(
            {"name": "Venta A", "amount": 10.0, "type_tax_use": "sale", "company_id": cls.company_a.id}
        )
        cls.tax_b = cls.env["account.tax"].create(
            {"name": "Venta B", "amount": 21.0, "type_tax_use": "sale", "company_id": cls.company_b.id}
        )
        # ``taxes_id`` is a plain many2many, not company-dependent: the product carries the
        # taxes of both companies and ``_filter_taxes_by_company`` picks the right one.
        cls.product = cls.env["product.product"].create(
            {"name": "Producto", "taxes_id": [Command.set((cls.tax_a + cls.tax_b).ids)]}
        )
        # Global and with no fiscal position: the company of an order carrying it is free
        # to change, which is the scenario, and a type cannot hold a position of a company
        # it does not belong to anyway (check_company).
        cls.plain_type = cls.env["sale.order.type"].sudo().create({"name": "Tipo sin posición", "company_id": False})

    def _create_order(self, company, order_type=None):
        return (
            self.env["sale.order"]
            .with_company(company)
            .create(
                {
                    # Explicit, so the create of ``sale_order_type`` does not reach into the
                    # type's sequence — which the accountman of the fixture cannot read.
                    "name": "SO-TEST",
                    "partner_id": self.customer.id,
                    "company_id": company.id,
                    "type_id": (order_type or self.plain_type).id,
                    "order_line": [Command.create({"product_id": self.product.id, "product_uom_qty": 1.0})],
                }
            )
            # Changing the company of an order is an administration move —on an
            # invoice it lives behind the pencil of ``account_multicompany_ux``— and what
            # these tests are about is the recomputation, not who is allowed to do it.
            .sudo()
        )

    def test_the_taxes_of_the_lines_follow_the_company(self):
        """What the "Update Taxes" button does, without asking for the click."""
        order = self._create_order(self.company_b)
        self.assertEqual(order.order_line.tax_ids, self.tax_b)

        order.write({"company_id": self.company_a.id})

        self.assertEqual(order.order_line.company_id, self.company_a)
        self.assertNotIn(self.tax_b, order.order_line.tax_ids)

    def test_a_confirmed_order_cannot_change_company_at_all(self):
        """Which is why the recomputation only targets orders that are not confirmed.

        Once the order is confirmed the ORM refuses the move outright: the lines carry the
        taxes of the previous company and ``tax_ids`` is ``check_company``. Recomputing them
        behind the user's back on a confirmed order would be papering over that, so the
        override leaves it to fail, and the guard on the state is what says so.
        """
        order = self._create_order(self.company_b)
        order.action_confirm()

        with self.assertRaisesRegex(UserError, "company"):
            order.write({"company_id": self.company_a.id})

    def test_a_write_that_does_not_touch_the_company_changes_nothing(self):
        order = self._create_order(self.company_b)

        order.write({"client_order_ref": "algo"})

        self.assertEqual(order.order_line.tax_ids, self.tax_b)

    def test_the_type_fiscal_position_wins_in_the_company_that_owns_it(self):
        fpos_b = (
            self.env["account.fiscal.position"]
            .sudo()
            .create({"name": "Posición de B", "company_id": self.company_b.id})
        )
        typed = (
            self.env["sale.order.type"]
            .sudo()
            .create({"name": "Tipo con posición", "company_id": self.company_b.id, "fiscal_position_id": fpos_b.id})
        )

        order = self._create_order(self.company_b, typed)

        self.assertEqual(order.fiscal_position_id, fpos_b)

    def test_each_order_of_a_batch_keeps_its_own_position(self):
        """The override did not iterate, so the value of one order reached the others."""
        fpos_b = (
            self.env["account.fiscal.position"]
            .sudo()
            .create({"name": "Posición de B", "company_id": self.company_b.id})
        )
        typed = (
            self.env["sale.order.type"]
            .sudo()
            .create({"name": "Tipo con posición", "company_id": self.company_b.id, "fiscal_position_id": fpos_b.id})
        )
        with_fpos = self._create_order(self.company_b, typed)
        without_fpos = self._create_order(self.company_b)

        (with_fpos + without_fpos)._compute_fiscal_position_id()

        self.assertEqual(with_fpos.fiscal_position_id, fpos_b)
        self.assertNotEqual(without_fpos.fiscal_position_id, fpos_b)
