#!/usr/bin/env python

from .models import Transaction
from datetime import datetime
import csv
import os
import re
from collections import defaultdict
from decimal import Decimal, getcontext

ABE_ROOT = 'abe'
PAYOUTS_DIR = os.path.join(ABE_ROOT, 'payouts')
TRANSACTIONS_FILE = os.path.join(ABE_ROOT, 'transactions.txt')


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
            name, email, amount = row
            email = email.strip()
            amount = Decimal(re.sub("[^0-9.]", "", amount))
            return email, amount


def read_payout_amounts():
    balances = defaultdict(int)
    payout_files = os.listdir(PAYOUTS_DIR)
    for payout_file in payout_files:
        email, amount = read_payout(payout_file)
        balances[email] += amount
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


def prepare_message(balances):
    balances_table = ""
    for name, balance in balances.items():
        balances_table += f"{name} | {balance:.2f}\n"
    message = f"""
    The current outstanding balances are:

    | Name | Balance |
    | ---- | --- |
    {balances_table}

    **Total** = {sum(balances.values()):.2f}
    """
    return "\r\n".join(line.strip() for line in message.split('\n')).strip()


def main():
    # set decimal precision at 10, to ensure
    # that it is the same everywhere
    # and large enough to be represent a sufficiently
    # large number of contributors
    getcontext().prec = 10

    owed = read_transaction_amounts()
    paid = read_payout_amounts()
    balances = compute_balances(owed, paid)
    message = prepare_message(balances)
    print(message)


if __name__ == "__main__":
    main()
