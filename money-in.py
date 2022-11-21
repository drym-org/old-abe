#!/usr/bin/env python

import csv
from decimal import Decimal
from dataclasses import astuple
import re
import os
from models import Transaction

PAYMENTS_DIR = 'payments'
TRANSACTIONS_FILE = 'transactions.txt'


def read_payment(payment_file):
    with open(os.path.join(PAYMENTS_DIR, payment_file)) as f:
        for row in csv.reader(f):
            name, email, amount = row
            amount = Decimal(re.sub("[^0-9.]", "", amount))
            return amount


def read_attributions():
    attributions = {}
    with open("attribution-example.txt") as f:
        for row in csv.reader(f):
            email, percentage = row
            percentage = Decimal(re.sub("[^0-9.]", "", percentage))
            attributions[email] = percentage / Decimal(100)
    assert sum(attributions.values()) == Decimal(1)
    return attributions


def find_unprocessed_payments():
    """
    1. Read the transactions file to find out which payments are already recorded as transactions
    2. Read the payments folder to get all payments
    3. find those which haven't been recorded and return those
    """
    recorded_payments = set()
    with open(TRANSACTIONS_FILE) as f:
        for _email, _amount, payment_file, _commit_hash, _created_at in csv.reader(f):
            recorded_payments.add(payment_file)
    all_payments = set(os.listdir(PAYMENTS_DIR))
    return all_payments.difference(recorded_payments)


def generate_transactions(amount, attributions, payment_file, commit_hash):
    transactions = []
    for email, percentage in attributions.items():
        t = Transaction(email, amount * percentage, payment_file, commit_hash)
        transactions.append(t)
    return transactions


def process_payment(payment_file):
    commit_hash = "DUMMY"
    amount = read_payment(payment_file)
    attributions = read_attributions()
    transactions = generate_transactions(amount, attributions, payment_file, commit_hash)
    with open(TRANSACTIONS_FILE, 'a') as f:
        writer = csv.writer(f)
        for row in transactions:
            writer.writerow(astuple(row))


def main():
    unprocessed_payments = find_unprocessed_payments()
    for payment_file in unprocessed_payments:
        process_payment(payment_file)


if __name__ == "__main__":
    main()
