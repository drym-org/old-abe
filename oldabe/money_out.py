#!/usr/bin/env python

from .models import Transaction, Debt
from datetime import datetime
import csv
import os
import re
from collections import defaultdict
from decimal import Decimal, getcontext

ABE_ROOT = 'abe'
PAYOUTS_DIR = os.path.join(ABE_ROOT, 'payouts')
TRANSACTIONS_FILE = os.path.join(ABE_ROOT, 'transactions.txt')
DEBTS_FILE = os.path.join(ABE_ROOT, 'debts.txt')


def read_transaction_amounts():
    balances = defaultdict(int)
    with open(TRANSACTIONS_FILE) as f:
        for row in csv.reader(f):
            t = Transaction(*row)
            t.amount = Decimal(t.amount)
            t.created_at = datetime.fromisoformat(t.created_at)
            balances[t.email] += t.amount
    return balances


def read_payout(payout_file):
    with open(os.path.join(PAYOUTS_DIR, payout_file)) as f:
        for row in csv.reader(f):
            name, _email, amount, _date = row
            amount = Decimal(re.sub("[^0-9.]", "", amount))
            return name, amount


def read_payout_amounts():
    balances = defaultdict(int)
    try:
        payout_files = os.listdir(PAYOUTS_DIR)
    except FileNotFoundError:
        payout_files = []
    for payout_file in payout_files:
        name, amount = read_payout(payout_file)
        balances[name] += amount
    return balances


def compute_balances(owed: dict, paid: dict):
    """
    Compute the balance owed to each contributor.
    """
    balances = defaultdict(int)
    for email in owed.keys():
        balance = owed[email] - paid[email]
        if balance > Decimal("0"):
            balances[email] = balance
    return balances


def prepare_balances_message(balances: dict):
    if not balances:
        return "There are no outstanding (payable) balances."
    balances_table = ""
    for name, balance in balances.items():
        balances_table += f"{name} | {balance:.2f}\n"
    message = f"""
    The current outstanding (payable) balances are:

    | Name | Balance |
    | ---- | --- |
    {balances_table}

    **Total** = {sum(balances.values()):.2f}
    """
    return "\r\n".join(line.strip() for line in message.split('\n')).strip()


def read_outstanding_debt_amounts():
    outstanding_debts = defaultdict(int)
    with open(DEBTS_FILE) as f:
        for row in csv.reader(f):
            d = Debt(*row)
            d.amount = Decimal(d.amount)
            d.amount_paid = Decimal(d.amount_paid)
            outstanding_amount = d.amount - d.amount_paid
            outstanding_debts[d.email] += outstanding_amount
    return outstanding_debts


def prepare_debts_message(outstanding_debts: dict):
    if not outstanding_debts:
        return "There are no outstanding (unpayable) debts."
    debts_table = ""
    for name, debt in outstanding_debts.items():
        debts_table += f"{name} | {debt:.2f}\n"
    message = f"""
    The current outstanding (unpayable) debts are:

    | Name | Debt |
    | ---- | --- |
    {debts_table}

    **Total** = {sum(outstanding_debts.values()):.2f}
    """
    return "\r\n".join(line.strip() for line in message.split('\n')).strip()


def combined_message(balances_message, debts_message):
    message = f"""
    {balances_message}

    ----------------------------

    {debts_message}
    """
    return "\r\n".join(line.strip() for line in message.split('\n')).strip()


def main():
    # set decimal precision at 10 to ensure
    # that it is the same everywhere
    # and large enough to represent a sufficiently
    # large number of contributors
    getcontext().prec = 10

    owed = read_transaction_amounts()
    paid = read_payout_amounts()
    balances = compute_balances(owed, paid)
    balances_message = prepare_balances_message(balances)
    outstanding_debts = read_outstanding_debt_amounts()
    debts_message = prepare_debts_message(outstanding_debts)
    print(combined_message(balances_message, debts_message))


if __name__ == "__main__":
    main()
