#!/usr/bin/env python

import csv
from decimal import Decimal, getcontext
from dataclasses import astuple
import re
import os
import subprocess
from .models import Transaction

ABE_ROOT = 'abe'
PAYMENTS_DIR = os.path.join(ABE_ROOT, 'payments')
NONATTRIBUTABLE_PAYMENTS_DIR = os.path.join(
    ABE_ROOT, 'payments', 'nonattributable'
)
TRANSACTIONS_FILE = os.path.join(ABE_ROOT, 'transactions.txt')
PRICE_FILE = os.path.join(ABE_ROOT, 'price.txt')
VALUATION_FILE = os.path.join(ABE_ROOT, 'valuation.txt')
ATTRIBUTIONS_FILE = os.path.join(ABE_ROOT, 'attributions.txt')


def read_payment(payment_file, payments_dir):
    with open(os.path.join(payments_dir, payment_file)) as f:
        for row in csv.reader(f, skipinitialspace=True):
            name, email, amount = row
            amount = Decimal(re.sub("[^0-9.]", "", amount))
            return email, amount


def read_price():
    with open(PRICE_FILE) as f:
        price = f.readline()
        price = Decimal(re.sub("[^0-9.]", "", price))
        return price


# note that commas are used as a decimal separator in some languages
# (e.g. Spain Spanish), so that would need to be handled at some point
def read_valuation():
    with open(VALUATION_FILE) as f:
        valuation = f.readline()
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


def get_payment_files(payments_dir):
    return {
        f
        for f in os.listdir(payments_dir)
        if not os.path.isdir(os.path.join(payments_dir, f))
    }


def find_unprocessed_payments(payments_dir):
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
    all_payments = get_payment_files(payments_dir)
    print("all payments")
    print(all_payments)
    return all_payments.difference(recorded_payments)


def generate_transactions(amount, attributions, payment_file, commit_hash):
    transactions = []
    for email, percentage in attributions.items():
        t = Transaction(email, amount * percentage, payment_file, commit_hash)
        transactions.append(t)
    return transactions


def total_amount_paid(for_email, payments_dir):
    payments = 0
    payment_files = get_payment_files(payments_dir)
    for payment_file in payment_files:
        email, amount = read_payment(payment_file, payments_dir)
        if email == for_email:
            payments += amount
    return payments


def generate_incoming_attribution(email, incoming_amount, price, valuation):
    total_payments = total_amount_paid(email, PAYMENTS_DIR)
    previous_total = total_payments - incoming_amount
    # how much of the incoming amount goes towards investment?
    incoming_investment = total_payments - max(price, previous_total)
    if incoming_investment > 0:
        share = incoming_investment / valuation
        return email, share
    else:
        return None


ROUNDING_TOLERANCE = Decimal("0.000001")


def get_rounding_difference(attributions):
    """ Due to finite precision, the Decimal module will round up or down
    on the last decimal place. This could result in the aggregate value not quite
    totaling to 1. This corrects that total by either adding or subtracting the
    difference from the incoming attribution.
    """
    total = sum(attributions.values())
    difference = total - Decimal(1)
    assert abs(difference) <= ROUNDING_TOLERANCE
    return difference


def renormalize(attributions, incoming_attribution):
    incoming_email, incoming_share = incoming_attribution
    target_proportion = Decimal(1) - incoming_share
    for email in attributions:
        # renormalize to reflect dilution
        attributions[email] *= target_proportion
    # add incoming share to existing investor or record new investor
    attributions[incoming_email] = (
        attributions.get(incoming_email, 0) + incoming_share
    )


def write_attributions(attributions):
    # format for output as percentages
    attributions = [
        (email, f'{share * Decimal(100):f}%')
        for email, share in attributions.items()
    ]
    with open(ATTRIBUTIONS_FILE, 'w') as f:
        writer = csv.writer(f)
        for row in attributions:
            writer.writerow(row)


def correct_rounding_error(attributions, incoming_attribution):
    incoming_email, _ = incoming_attribution
    difference = get_rounding_difference(attributions)
    attributions[incoming_email] -= difference


def update_attributions(incoming_attribution, attributions):
    renormalize(attributions)
    correct_rounding_error(attributions, incoming_attribution)
    write_attributions(attributions)


def update_transactions(transactions):
    with open(TRANSACTIONS_FILE, 'a') as f:
        writer = csv.writer(f)
        for row in transactions:
            writer.writerow(astuple(row))


def update_valuation(valuation, amount):
    new_valuation = valuation + amount
    with open(VALUATION_FILE, 'w') as f:
        writer = csv.writer(f)
        writer.writerow((new_valuation,))
    return new_valuation


def get_git_revision_short_hash() -> str:
    """From https://stackoverflow.com/a/21901260"""
    return (
        subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'])
        .decode('ascii')
        .strip()
    )


def process_payment(payment_file, valuation, price, attributable=True):
    payments_dir = (
        PAYMENTS_DIR if attributable else NONATTRIBUTABLE_PAYMENTS_DIR
    )
    commit_hash = get_git_revision_short_hash()
    email, amount = read_payment(payment_file, payments_dir)
    attributions = read_attributions()
    transactions = generate_transactions(
        amount, attributions, payment_file, commit_hash
    )
    update_transactions(transactions)
    valuation = update_valuation(valuation, amount)
    if attributable:
        incoming_attribution = generate_incoming_attribution(
            email, amount, price, valuation
        )
        if incoming_attribution:
            update_attributions(incoming_attribution, attributions)


def main():

    getcontext().prec = 10

    unprocessed_payments = find_unprocessed_payments(PAYMENTS_DIR)
    price = read_price()
    valuation = read_valuation()
    print(unprocessed_payments)
    for payment_file in unprocessed_payments:
        print(payment_file)
        process_payment(payment_file, valuation, price, attributable=True)
    try:
        unprocessed_nonattributable_payments = find_unprocessed_payments(
            NONATTRIBUTABLE_PAYMENTS_DIR
        )
    except FileNotFoundError:
        unprocessed_nonattributable_payments = []
    for payment_file in unprocessed_nonattributable_payments:
        process_payment(payment_file, valuation, price, attributable=False)


if __name__ == "__main__":
    main()
