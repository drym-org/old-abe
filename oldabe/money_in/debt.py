import dataclasses
from itertools import accumulate
from typing import Iterable, List, Set
from ..models import Debt
from ..tally import Tally
from decimal import Decimal
from ..distribution import Distribution
from ..models import Payment


def create_debts(
    available_amount: Decimal,
    distribution: Distribution,
    payable_contributors: Set[str],
    payment: Payment,
):
    return [
        Debt(
            email=email,
            amount=amount,
            payment_file=payment.file,
        )
        for email, amount in distribution.distribute(available_amount).items()
        if (email not in payable_contributors and amount > Decimal(0))
    ]


# TODO: should we generate separate transactions for money paid
# for debt vs as a normal payout?
def pay_outstanding_debts(
    payment: Payment,
    all_debts: Iterable[Debt],
    payable_contributors: Set[str],
) -> List[Debt]:
    """
    Given an available amount return debt payments for as many debts as can
    be covered
    """
    # We are assuming debts are being processed in chronological order
    # because they are written in chronological order in the single debts
    # table in the debts file (i.e., it is a FileRepo), so we don't need
    # to sort them by date.

    # compute the negative balance, i.e., the total of the negative debts,
    # by user
    debt_payment_totals_by_user = Tally(
        (d.email, d.amount) for d in all_debts if d.amount < 0
    )
    # go through and remove (or add to a new list) as many of the positive
    # debts as we can, in order, from the beginning
    # this gives us our sorted list of unpaid debts
    # which we can then go through in order and pay off
    unpaid_debts = []
    for d in all_debts:
        if d.amount < 0:
            continue
        # this debt is completely unpaid
        elif debt_payment_totals_by_user[d.email] == 0:
            unpaid_debts.append(d)
        # this debt is fully paid
        elif debt_payment_totals_by_user[d.email] >= d.amount:
            debt_payment_totals_by_user[d.email] -= d.amount
        # this debt is partially paid
        else:
            # if one debt is only partially paid, then replace it with a new
            # debt showing the partial balance
            partial_debt = dataclasses.replace(
                d, amount=d.amount - debt_payment_totals_by_user[d.email]
            )
            debt_payment_totals_by_user[d.email] = 0
            unpaid_debts.append(partial_debt)

    available_amount = payment.amount
    payable_debts = [
        d for d in unpaid_debts if d.email in payable_contributors
    ]

    accumulated_amount = list(
        accumulate((d.amount for d in payable_debts), initial=0)
    )
    cumulative_debt = [
        amount for amount in accumulated_amount if amount <= available_amount
    ]

    return [
        Debt(
            email=d.email,
            amount=-amount,  # negative debt (i.e., debt payment)
            payment_file=payment.file,
        )
        for d, paid_so_far in zip(payable_debts, cumulative_debt)
        if (amount := min(d.amount, available_amount - paid_so_far))
        > Decimal(0)
    ]
