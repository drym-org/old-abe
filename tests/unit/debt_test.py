import dataclasses
from datetime import datetime
from decimal import Decimal

import time_machine

from oldabe.models import Debt, DebtPayment, Payment
from oldabe.distribution import Distribution
from oldabe.money_in.debt import (
    pay_outstanding_debts,
    create_debts,
    update_debts,
)


class TestCreateDebts:
    @time_machine.travel(datetime.now(), tick=False)
    def test_debt_for_unpayable_contributor(self):
        distribution = Distribution(
            {
                "payable@example.com": 70,
                "unpayable@example.com": 30,
            }
        )
        payment = Payment(
            email="fake@test.com",
            name="Fake",
            amount=Decimal(100),
            file="fake.txt",
        )

        debts = create_debts(
            available_amount=payment.amount,
            distribution=distribution,
            payable_contributors=set(["payable@example.com"]),
            payment=payment,
        )

        assert debts == [
            Debt(
                email="unpayable@example.com",
                amount=Decimal("30.00"),
                amount_paid=Decimal(0),
                payment_file=payment.file,
            )
        ]

    def test_no_unpayable_contibutors(self):
        distribution = Distribution(
            {
                "payable@example.com": 70,
                "payable2@example.com": 30,
            }
        )
        payment = Payment(
            email="fake@test.com",
            name="Fake",
            amount=Decimal(100),
            file="fake.txt",
        )

        debts = create_debts(
            available_amount=payment.amount,
            distribution=distribution,
            payable_contributors=set(
                ["payable@example.com", "payable2@example.com"]
            ),
            payment=payment,
        )

        assert debts == []

    def test_no_available_amount(self):
        distribution = Distribution(
            {
                "payable@example.com": 70,
                "unpayable@example.com": 30,
            }
        )
        payment = Payment(
            email="fake@test.com",
            name="Fake",
            amount=Decimal(100),
            file="fake.txt",
        )

        debts = create_debts(
            available_amount=Decimal(0),
            distribution=distribution,
            payable_contributors=set(["payable@example.com"]),
            payment=payment,
        )

        assert debts == []


class TestPayOutstandingDebts:
    def test_pay_one(self):
        single_debt = Debt(
            email="payable@example.com",
            amount=Decimal(10),
            amount_paid=Decimal(0),
            payment_file="fake-file",
        )

        debt_payments = pay_outstanding_debts(
            available_amount=Decimal(single_debt.amount),
            all_debts=[single_debt],
            payable_contributors=set([single_debt.email]),
        )

        assert debt_payments == [
            DebtPayment(amount=single_debt.amount, debt=single_debt)
        ]

    def test_pay_multiple(self):
        debts = [
            Debt(
                email="payable@example.com",
                amount=Decimal(10),
                amount_paid=Decimal(0),
                payment_file="fake-file",
            ),
            Debt(
                email="payable@example.com",
                amount=Decimal(10),
                amount_paid=Decimal(0),
                payment_file="fake-file",
            ),
        ]

        debt_payments = pay_outstanding_debts(
            available_amount=Decimal(20),
            all_debts=debts,
            payable_contributors=set(["payable@example.com"]),
        )

        assert debt_payments == [
            DebtPayment(amount=d.amount, debt=d) for d in debts
        ]

    def test_pay_partial(self):
        debts = [
            Debt(
                email="payable@example.com",
                amount=Decimal(10),
                amount_paid=Decimal(0),
                payment_file="fake-file",
            ),
            Debt(
                email="payable@example.com",
                amount=Decimal(10),
                amount_paid=Decimal(0),
                payment_file="fake-file",
            ),
        ]

        debt_payments = pay_outstanding_debts(
            available_amount=Decimal(15),
            all_debts=debts,
            payable_contributors=set(["payable@example.com"]),
        )

        assert debt_payments == [
            DebtPayment(amount=Decimal(10), debt=debts[0]),
            DebtPayment(amount=Decimal(5), debt=debts[1]),
        ]

    def test_skip_unpayable(self):
        debts = [
            Debt(
                email="payable@example.com",
                amount=Decimal(10),
                amount_paid=Decimal(0),
                payment_file="fake-file",
            ),
            Debt(
                email="unpayable@example.com",
                amount=Decimal(10),
                amount_paid=Decimal(0),
                payment_file="fake-file",
            ),
            Debt(
                email="payable@example.com",
                amount=Decimal(10),
                amount_paid=Decimal(0),
                payment_file="fake-file",
            ),
        ]

        debt_payments = pay_outstanding_debts(
            available_amount=Decimal(20),
            all_debts=debts,
            payable_contributors=set(["payable@example.com"]),
        )

        assert debt_payments == [
            DebtPayment(amount=d.amount, debt=d)
            for d in debts
            if d.email != "unpayable@example.com"
        ]

    def test_no_debts(self):
        debt_payments = pay_outstanding_debts(
            available_amount=Decimal(20),
            all_debts=[],
            payable_contributors=set(["payable@example.com"]),
        )

        assert debt_payments == []

    def test_no_amount(self):
        debts = [
            Debt(
                email="payable@example.com",
                amount=Decimal(10),
                amount_paid=Decimal(0),
                payment_file="fake-file",
            ),
            Debt(
                email="payable@example.com",
                amount=Decimal(10),
                amount_paid=Decimal(0),
                payment_file="fake-file",
            ),
        ]

        debt_payments = pay_outstanding_debts(
            available_amount=Decimal(0),
            all_debts=debts,
            payable_contributors=set(["payable@example.com"]),
        )

        assert debt_payments == []


class TestUpdateDebts:
    def test_add_debts(self):
        existing_debts = [
            Debt(
                email="payable@example.com",
                amount=Decimal(10),
                amount_paid=Decimal(0),
                payment_file="fake-file",
            ),
        ]
        new_debts = [
            Debt(
                email="payable@example.com",
                amount=Decimal(10),
                amount_paid=Decimal(0),
                payment_file="fake-file",
            ),
        ]

        updated_debts = update_debts(
            existing_debts=existing_debts,
            new_debts=new_debts,
            debt_payments=[],
        )

        assert updated_debts == existing_debts + new_debts

    def test_pay_debts(self):
        existing_debts = [
            Debt(
                email="payable@example.com",
                amount=Decimal(10),
                amount_paid=Decimal(0),
                payment_file="fake-file",
            ),
            Debt(
                email="payable@example.com",
                amount=Decimal(5),
                amount_paid=Decimal(0),
                payment_file="fake-file-ii",
            ),
        ]
        debt_payments = [
            DebtPayment(
                amount=Decimal(10),
                debt=existing_debts[0],
            )
        ]

        updated_debts = update_debts(
            existing_debts=existing_debts,
            new_debts=[],
            debt_payments=debt_payments,
        )

        assert updated_debts == [
            dataclasses.replace(
                existing_debts[0], amount_paid=debt_payments[0].amount
            ),
            existing_debts[1],
        ]

    def test_pay_debts_already_partially_paid(self):
        existing_debts = [
            Debt(
                email="payable@example.com",
                amount=Decimal(10),
                amount_paid=Decimal(5),
                payment_file="fake-file",
            ),
            Debt(
                email="payable@example.com",
                amount=Decimal(10),
                amount_paid=Decimal(0),
                payment_file="fake-file-ii",
            ),
        ]
        debt_payments = [
            DebtPayment(
                amount=Decimal(2),
                debt=existing_debts[0],
            )
        ]

        updated_debts = update_debts(
            existing_debts=existing_debts,
            new_debts=[],
            debt_payments=debt_payments,
        )

        assert updated_debts == [
            dataclasses.replace(existing_debts[0], amount_paid=Decimal(7)),
            existing_debts[1],
        ]

    def test_apply_multiple_payments(self):
        existing_debts = [
            Debt(
                email="payable@example.com",
                amount=Decimal(10),
                amount_paid=Decimal(5),
                payment_file="fake-file",
            ),
            Debt(
                email="payable@example.com",
                amount=Decimal(10),
                amount_paid=Decimal(0),
                payment_file="fake-file-ii",
            ),
        ]
        debt_payments = [
            DebtPayment(
                amount=Decimal(2),
                debt=existing_debts[0],
            )
        ]

        updated_debts = update_debts(
            existing_debts=existing_debts,
            new_debts=[],
            debt_payments=debt_payments,
        )

        assert updated_debts == [
            dataclasses.replace(existing_debts[0], amount_paid=Decimal(7)),
            existing_debts[1],
        ]
