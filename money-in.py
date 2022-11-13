#!/usr/bin/env python

import csv
from decimal import Decimal
from dataclasses import astuple
import re
from models import Transaction


def read_payment(payment_file):
    with open(payment_file) as f:
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


def generate_transactions(amount, attributions, payment_file, commit_hash):
    transactions = []
    for email, percentage in attributions.items():
        t = Transaction(email, amount * percentage, payment_file, commit_hash)
        transactions.append(t)
    return transactions


def main():
    payment_file = "payments-example.txt"
    commit_hash = "DUMMY"
    amount = read_payment(payment_file)
    attributions = read_attributions()
    transactions = generate_transactions(amount, attributions, payment_file, commit_hash)
    with open('transactions.txt', 'a') as f:
        writer = csv.writer(f)
        for row in transactions:
            writer.writerow(astuple(row))


if __name__ == "__main__":
    main()
