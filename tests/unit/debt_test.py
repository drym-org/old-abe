import dataclasses
from datetime import datetime
from decimal import Decimal
from fractions import Fraction

import time_machine

from oldabe.models import Debt, Payment
from oldabe.distribution import Distribution
from oldabe.money_in.debt import (
    pay_outstanding_debts,
    create_debts,
)


class TestCreateDebts:
    @time_machine.travel(datetime.now(), tick=False)
    def test_debt_for_unpayable_contributor(self):
        distribution = Distribution(
            {
                "payable@example.com": Fraction(7, 10),
                "unpayable@example.com": Fraction(3, 10),
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
                payment_file=payment.file,
            )
        ]

    def test_no_unpayable_contibutors(self):
        distribution = Distribution(
            {
                "payable@example.com": Fraction(7, 10),
                "payable2@example.com": Fraction(3, 10),
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
                "payable@example.com": Fraction(7, 10),
                "unpayable@example.com": Fraction(3, 10),
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
    @time_machine.travel(datetime.now(), tick=False)
    def test_pay_one(self):
        single_debt = Debt(
            email="payable@example.com",
            amount=Decimal(10),
            payment_file="fake-file",
        )
        payment = Payment(
            email="payer@example.com", name="Sam", amount=Decimal(100)
        )

        debt_payments = pay_outstanding_debts(
            payment=payment,
            all_debts=[single_debt],
            payable_contributors=set([single_debt.email]),
        )

        assert debt_payments == [
            Debt(
                email=single_debt.email,
                amount=-single_debt.amount,
                payment_file=payment.file,
            )
        ]

    # TODO: fix these remaining tests like test_pay_one above

    @time_machine.travel(datetime.now(), tick=False)
    def test_pay_multiple(self):
        debts = [
            Debt(
                email="payable@example.com",
                amount=Decimal(10),
                payment_file="fake-file",
            ),
            Debt(
                email="payable@example.com",
                amount=Decimal(10),
                payment_file="fake-file",
            ),
        ]
        payment = Payment(
            email="payer@example.com", name="Sam", amount=Decimal(20)
        )

        debt_payments = pay_outstanding_debts(
            payment=payment,
            all_debts=debts,
            payable_contributors=set(["payable@example.com"]),
        )

        assert debt_payments == [
            Debt(email=d.email, amount=-d.amount, payment_file=payment.file)
            for d in debts
        ]

    @time_machine.travel(datetime.now(), tick=False)
    def test_debts_are_paid_in_order(self):
        # note this also tests paying separate people
        debts = [
            Debt(
                email="payable1@example.com",
                amount=Decimal(10),
                payment_file="fake-file",
            ),
            Debt(
                email="payable2@example.com",
                amount=Decimal(10),
                payment_file="fake-file",
            ),
        ]

        payment = Payment(
            email="payer@example.com", name="Sam", amount=Decimal(10)
        )

        debt_payments = pay_outstanding_debts(
            payment=payment,
            all_debts=debts,
            payable_contributors=set(
                ["payable1@example.com", "payable2@example.com"]
            ),
        )

        assert debt_payments == [
            Debt(
                email=debts[0].email,
                amount=-debts[0].amount,
                payment_file=payment.file,
            )
        ]

    @time_machine.travel(datetime.now(), tick=False)
    def test_pay_partial(self):
        debts = [
            Debt(
                email="payable1@example.com",
                amount=Decimal(10),
                payment_file="fake-file",
            ),
            Debt(
                email="payable2@example.com",
                amount=Decimal(10),
                payment_file="fake-file",
            ),
        ]

        payment = Payment(
            email="payer@example.com", name="Sam", amount=Decimal(15)
        )

        debt_payments = pay_outstanding_debts(
            payment=payment,
            all_debts=debts,
            payable_contributors=set(
                ["payable1@example.com", "payable2@example.com"]
            ),
        )

        assert debt_payments == [
            Debt(
                email=debts[0].email,
                amount=-Decimal(10),
                payment_file=payment.file,
            ),
            Debt(
                email=debts[1].email,
                amount=-Decimal(5),
                payment_file=payment.file,
            ),
        ]

    @time_machine.travel(datetime.now(), tick=False)
    def test_skip_unpayable(self):
        debts = [
            Debt(
                email="payable@example.com",
                amount=Decimal(10),
                payment_file="fake-file",
            ),
            Debt(
                email="unpayable@example.com",
                amount=Decimal(10),
                payment_file="fake-file",
            ),
            Debt(
                email="payable@example.com",
                amount=Decimal(10),
                payment_file="fake-file",
            ),
        ]

        payment = Payment(
            email="payer@example.com", name="Sam", amount=Decimal(20)
        )

        debt_payments = pay_outstanding_debts(
            payment=payment,
            all_debts=debts,
            payable_contributors=set(["payable@example.com"]),
        )

        assert debt_payments == [
            Debt(email=d.email, amount=-d.amount, payment_file=payment.file)
            for d in debts
            if d.email != "unpayable@example.com"
        ]

    def test_no_debts(self):
        payment = Payment(
            email="payer@example.com", name="Sam", amount=Decimal(20)
        )

        debt_payments = pay_outstanding_debts(
            payment=payment,
            all_debts=[],
            payable_contributors=set(["payable@example.com"]),
        )

        assert debt_payments == []

    def test_no_amount(self):
        debts = [
            Debt(
                email="payable@example.com",
                amount=Decimal(10),
                payment_file="fake-file",
            ),
            Debt(
                email="payable@example.com",
                amount=Decimal(10),
                payment_file="fake-file",
            ),
        ]

        payment = Payment(
            email="payer@example.com", name="Sam", amount=Decimal(0)
        )

        debt_payments = pay_outstanding_debts(
            payment=payment,
            all_debts=debts,
            payable_contributors=set(["payable@example.com"]),
        )

        assert debt_payments == []
