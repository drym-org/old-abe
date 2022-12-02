#!/usr/bin/env python

import csv
from decimal import Decimal
from dataclasses import astuple
import re
import os
from models import Transaction

PAYMENTS_DIR = 'payments'
TRANSACTIONS_FILE = 'transactions.txt'
PRICE_FILE = 'price.txt'
VALUATION_FILE = 'valuation.txt'
ATTRIBUTIONS_FILE = 'attribution-example.txt'


def read_payment(payment_file):
    with open(os.path.join(PAYMENTS_DIR, payment_file)) as f:
        for row in csv.reader(f, skipinitialspace=True):
            name, email, amount = row
            amount = Decimal(re.sub("[^0-9.]", "", amount))
            return email, amount


def read_price():
    with open(PRICE_FILE) as f:
        for row in csv.reader(f):
            price = row[0]
            price = Decimal(re.sub("[^0-9.]", "", price))
            return price


# note that commas are used as a decimal separator in some languages
# (e.g. Spain Spanish), so that would need to be handled at some point
def read_valuation():
    with open(VALUATION_FILE) as f:
        for row in csv.reader(f):
            valuation = row[0]
            valuation = Decimal(re.sub("[^0-9.]", "", valuation))
            return valuation


def read_attributions():
    attributions = {}
    with open(ATTRIBUTIONS_FILE) as f:
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
        for (
            _email,
            _amount,
            payment_file,
            _commit_hash,
            _created_at,
        ) in csv.reader(f):
            recorded_payments.add(payment_file)
    all_payments = set(os.listdir(PAYMENTS_DIR))
    return all_payments.difference(recorded_payments)


def generate_transactions(amount, attributions, payment_file, commit_hash):
    transactions = []
    for email, percentage in attributions.items():
        t = Transaction(email, amount * percentage, payment_file, commit_hash)
        transactions.append(t)
    return transactions


def total_amount_paid(for_email):
    payments = 0
    payment_files = os.listdir(PAYMENTS_DIR)
    for payment_file in payment_files:
        email, amount = read_payment(payment_file)
        if email == for_email:
            payments += amount
    return payments


def generate_incoming_attribution(email, current_amount, price, valuation):
    total_amount = total_amount_paid(email)
    investment = total_amount - price
    if investment > 0:
        max_share = investment / valuation * 100
        share = current_amount / investment * max_share
        return email, share
    else:
        return None


def update_attributions(incoming_attribution, attributions):
    incoming_email, incoming_share = incoming_attribution
    target_proportion = (Decimal(100) - incoming_share) / Decimal(100)
    # renormalize
    attributions = [(email, share * target_proportion * Decimal(100))
                    for email, share in attributions.items()]
    # add incoming share
    attributions = [(email, share + (incoming_share if email == incoming_email else 0))
                    for email, share in attributions]
    attributions = [(email, f'{share:.2f}%')
                    for email, share in attributions]
    with open(ATTRIBUTIONS_FILE, 'w') as f:
        writer = csv.writer(f)
        for row in attributions:
            writer.writerow(row)


def update_transactions(transactions):
    with open(TRANSACTIONS_FILE, 'a') as f:
        writer = csv.writer(f)
        for row in transactions:
            writer.writerow(astuple(row))


def process_payment(payment_file, valuation, price):
    commit_hash = "DUMMY"
    email, amount = read_payment(payment_file)
    attributions = read_attributions()
    transactions = generate_transactions(
        amount, attributions, payment_file, commit_hash
    )
    update_transactions(transactions)
    incoming_attribution = generate_incoming_attribution(email,
                                                         amount,
                                                         price,
                                                         valuation)
    if incoming_attribution:
        update_attributions(incoming_attribution, attributions)


def main():
    unprocessed_payments = find_unprocessed_payments()
    price = read_price()
    valuation = read_valuation()
    for payment_file in unprocessed_payments:
        process_payment(payment_file, valuation, price)


if __name__ == "__main__":
    main()
