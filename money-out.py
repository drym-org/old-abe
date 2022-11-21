#!/usr/bin/env python

from models import Transaction
from datetime import datetime
import csv
import os
import re
from collections import defaultdict
from decimal import Decimal

PAYOUTS_DIR = 'payouts'
TRANSACTIONS_FILE = 'transactions.txt'


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
    with open(payout_file) as f:
        for row in csv.reader(f):
            name, email, amount = row
            email = email.strip()
            amount = Decimal(re.sub("[^0-9.]", "", amount))
            return email, amount


def read_payout_amounts():
    balances = defaultdict(int)
    payout_files = os.listdir(PAYOUTS_DIR)
    for payout_file in payout_files:
        email, amount = read_payout(os.path.join(PAYOUTS_DIR, payout_file))
        balances[email] += amount
    return balances


def compute_balances(owed, paid):
    balances = defaultdict(int)
    for email in owed.keys():
        balance = owed[email] - paid[email]
        if balance > Decimal(0):
            balances[email] = balance
    return balances


def main():
    owed = read_transaction_amounts()
    paid = read_payout_amounts()
    balances = compute_balances(owed, paid)
    print(balances)


if __name__ == "__main__":
    main()
