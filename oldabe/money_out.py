#!/usr/bin/env python

from .models import Transaction, Debt, Advance, Payout, row_to_model
import csv
import os
from collections import defaultdict
from decimal import getcontext
from .constants import (
    DECIMAL_PRECISION,
    PAYOUTS_DIR,
    TRANSACTIONS_FILE,
    DEBTS_FILE,
    ADVANCES_FILE,
)


def read_owed_amounts():
    balances = defaultdict(int)
    with open(TRANSACTIONS_FILE) as f:
        for row in csv.reader(f):
            t = row_to_model(row, Transaction)
            balances[t.email] += t.amount
    return balances


def read_payout(payout_file):
    with open(os.path.join(PAYOUTS_DIR, payout_file)) as f:
        for row in csv.reader(f):
            payout = row_to_model(row, Payout)
            return payout


def read_paid_amounts():
    paid = defaultdict(int)
    try:
        payout_files = os.listdir(PAYOUTS_DIR)
    except FileNotFoundError:
        payout_files = []
    for payout_file in payout_files:
        payout = read_payout(payout_file)
        paid[payout.name] += payout.amount
    return paid


def compute_balances(owed: dict, paid: dict):
    """
    Compute the balance owed to each contributor.
    """
    return {
        email: owed[email] - paid[email]
        for email in owed.keys()
        if owed[email] > paid[email]
    }


def prepare_balances_message(balances: dict):
    if not balances:
        return "There are no outstanding (payable) balances."

    return "\n".join(
        "The current outstanding (payable) balances are:",
        "",
        "| Name | Balance |",
        "| ---- | --- |",
        *(f"{name} | {balance:.2f}" for name, balance in balances.items()),
        "",
        f"**Total** = {sum(balances.values()):.2f}",
    )


def read_outstanding_debt_amounts():
    outstanding_amounts = defaultdict(int)
    with open(DEBTS_FILE) as f:
        for row in csv.reader(f):
            d = row_to_model(row, Debt)
            outstanding_amount = d.amount - d.amount_paid
            outstanding_amounts[d.email] += outstanding_amount
    return outstanding_amounts


def prepare_debts_message(outstanding_debts: dict):
    if not outstanding_debts:
        return "There are no outstanding (unpayable) debts."

    return "\n".join(
        "The current outstanding (unpayable) debts are:",
        "",
        "| Name | Debt |",
        "| ---- | --- |",
        *(f"{name} | {debt:.2f}" for name, debt in outstanding_debts.items()),
        "",
        f"**Total** = {sum(outstanding_debts.values()):.2f}",
    )


def read_advance_amounts():
    amounts = defaultdict(int)
    with open(ADVANCES_FILE) as f:
        for row in csv.reader(f):
            a = Advance(*row)
            amounts[a.email] += a.amount
    return amounts


def prepare_advances_message(advances: dict):
    """A temporary message reporting aggregate advances, for testing purposes."""
    if not advances:
        return "There are no advances."

    return "\n".join(
        "The current advances are:",
        "",
        "| Name | Advance |",
        "| ---- | --- |",
        *(f"{name} | {advance:.2f}" for name, advance in advances.items()),
        "",
        f"**Total** = {sum(advances.values()):.2f}",
    )


def combined_message(balances_message, debts_message, advances_message):
    return "\n".join(
        f"{balances_message}",
        "",
        "----------------------------",
        "",
        f"{debts_message}",
        "",
        "----------------------------",
        "",
        f"{advances_message}",
    )


def main():
    # set decimal precision at 10 to ensure
    # that it is the same everywhere
    # and large enough to represent a sufficiently
    # large number of contributors
    getcontext().prec = DECIMAL_PRECISION

    owed = read_owed_amounts()
    paid = read_paid_amounts()
    balances = compute_balances(owed, paid)
    balances_message = prepare_balances_message(balances)

    outstanding_debts = read_outstanding_debt_amounts()
    debts_message = prepare_debts_message(outstanding_debts)

    advances = read_advance_amounts()
    advances_message = prepare_advances_message(advances)

    print(combined_message(balances_message, debts_message, advances_message))


if __name__ == "__main__":
    main()
