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


def parse_percentage(value):
    '''
    Translates values expressed in percentage format (75.234) into
    their decimal equivalents (0.75234). This effectively divides
    the value by 100 without losing precision.
    '''
    value = re.sub("[^0-9.]", "", value)
    value = "00" + value
    if "." not in value:
        value = value + ".0"
    value = re.sub(
        r"(?P<pre>\d{2})\.(?P<post>\d+)", r".\g<pre>\g<post>", value
    )
    value = Decimal(value)
    return value


def serialize_proportion(value):
    '''
    Translates values expressed in decimal format (0.75234) into
    their percentage equivalents (75.234). This effectively multiplies
    the value by 100 without losing precision.
    '''
    # otherwise, decimal gets translated '2E-7.0'
    value = format(value, "f")
    if "." in value:
        value = value + "0"
    else:
        value = value + ".0"
    value = re.sub(
        r"(?P<pre>\d)\.(?P<post>\d{2})(?P<rest>\d*)",
        r"\g<pre>\g<post>.\g<rest>0",  # note trailing zero
        value,
    )
    value = re.sub(r"^0+(\d*)", r"\1", value)
    value = re.sub(r"^\.", r"0.", value)
    return value


def read_payment(payment_file, attributable=True):
    payments_dir = PAYMENTS_DIR if attributable else NONATTRIBUTABLE_PAYMENTS_DIR
    with open(os.path.join(payments_dir, payment_file)) as f:
        for row in csv.reader(f, skipinitialspace=True):
            name, email, amount = row
            amount = re.sub("[^0-9.]", "", amount)
            return Payment(email, Decimal(amount), attributable, payment_file)


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
            attributions[email] = parse_percentage(percentage)
    assert sum(attributions.values()) == Decimal("1")
    return attributions


def get_payment_files(attributable=True):
    payments_dir = PAYMENTS_DIR if attributable else NONATTRIBUTABLE_PAYMENTS_DIR
    return {
        f
        for f in os.listdir(payments_dir)
        if not os.path.isdir(os.path.join(payments_dir, f))
    }


def find_unprocessed_payments(attributable=True):
    """
    1. Read the transactions file to find out which payments are already
       recorded as transactions
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
    all_payments = get_payment_files(attributable)
    print("all payments")
    print(all_payments)
    return all_payments.difference(recorded_payments)


def generate_transactions(amount, attributions, payment_file, commit_hash):
    transactions = []
    for email, percentage in attributions.items():
        t = Transaction(email, amount * percentage, payment_file, commit_hash)
        transactions.append(t)
    return transactions


def total_amount_paid(for_email, attributable=True):
    payments = 0
    payment_files = get_payment_files(attributable)
    for payment_file in payment_files:
        payment = read_payment(payment_file, attributable)
        if payment.email == for_email:
            payments += payment.amount
    return payments


def calculate_incoming_investment(email, incoming_amount, price):
    total_payments = total_amount_paid(email, attributable=True)
    previous_total = total_payments - incoming_amount
    # how much of the incoming amount goes towards investment?
    incoming_investment = total_payments - max(price, previous_total)
    return max(0, incoming_investment)


def calculate_incoming_attribution(email, incoming_investment, valuation):
    '''
    If there is an incoming investment, find out what proportion it
    represents of the overall valuation of the project.
    '''
    if incoming_investment > 0:
        # TODO - do we need to wrap anything in a Decimal here?
        share = incoming_investment / valuation
        return email, share
    else:
        return None


ROUNDING_TOLERANCE = Decimal("0.000001")


def get_rounding_difference(attributions):
    """Due to finite precision, the Decimal module will round up or down
    on the last decimal place. This could result in the aggregate value not
    quite totaling to 1. This corrects that total by either adding or
    subtracting the difference from the incoming attribution.
    """
    total = sum(attributions.values())
    difference = total - Decimal("1")
    assert abs(difference) <= ROUNDING_TOLERANCE
    return difference


def renormalize(attributions, incoming_attribution):
    incoming_email, incoming_share = incoming_attribution
    target_proportion = Decimal("1") - incoming_share
    for email in attributions:
        # renormalize to reflect dilution
        attributions[email] *= target_proportion
    # add incoming share to existing investor or record new investor
    attributions[incoming_email] = (
        attributions.get(incoming_email, 0) + incoming_share
    )


def write_attributions(attributions):
    # don't write attributions if they aren't normalized
    assert sum(attributions.values()) == Decimal("1")
    # format for output as percentages
    # BUG: this step causes the result to lose precision
    # and not total to 100 exactly, since some trailing
    # decimal positions are lost after multiplying by 100.
    attributions = [
        (email, serialize_proportion(share))
        for email, share in attributions.items()
    ]
    with open(ATTRIBUTIONS_FILE, 'w') as f:
        writer = csv.writer(f)
        for row in attributions:
            writer.writerow(row)


def correct_rounding_error(attributions, incoming_email):
    difference = get_rounding_difference(attributions)
    attributions[incoming_email] -= difference


def update_attributions(incoming_attribution, attributions):
    renormalize(attributions, incoming_attribution)
    correct_rounding_error(attributions, incoming_attribution[0])
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


def process_payment(payment, valuation, price):
    """
    Process a (new) payment.

    First, we record owed amounts to existing contributors from the payment.
    To do that, we consult the attribution file and determine how much is owed
    to each contributor based on the current percentages, generating a
    fresh entry in the transactions file for each contributor.

    Then, if the payment is "attributable" (the default), we determine
    if some portion of it counts as an investment in the project. If it does,
    then the valuation is inflated by the investment amount, and the payer is
    attributed a share commensurate with their investment, diluting the
    attributions.

    If the payment is not attributable, then the entire amount is treated
    as compensation and no component of it counts towards investment. This
    is typically the case for attributive revenue, that is, revenue from
    downstream projects that recognize the present project in their
    attributions.
    """
    email, amount = payment.email, payment.amount
    commit_hash = get_git_revision_short_hash()

    # figure out how much each person in the attributions file is owed from
    # this payment, generating a transaction for each stakeholder.
    attributions = read_attributions()
    transactions = generate_transactions(
        amount, attributions, payment.file, commit_hash
    )
    update_transactions(transactions)
    if payment.attributable:
        incoming_investment = calculate_incoming_investment(
            email, amount, price
        )
        # inflate valuation by the amount of the fresh investment
        valuation = update_valuation(valuation, incoming_investment)
        incoming_attribution = calculate_incoming_attribution(
            email, incoming_investment, valuation
        )
        if incoming_attribution:
            # dilute attributions
            update_attributions(incoming_attribution, attributions)


def main():
    # Set the decimal precision explicitly so that we can
    # be sure that it is the same regardless of where
    # it is run, to avoid any possible accounting errors
    getcontext().prec = 10

    # Find all payments that have not already been processed, that
    # is, which do not appear in the transactions file.
    unprocessed_payments = find_unprocessed_payments(attributable=True)
    price = read_price()
    valuation = read_valuation()
    print(unprocessed_payments)
    for payment_file in unprocessed_payments:
        print(payment_file)

        payment = read_payment(payment_file, attributable=True)

        process_payment(payment, valuation, price, attributable=True)
    try:
        unprocessed_nonattributable_payments = find_unprocessed_payments(
            attributable=False
        )
    except FileNotFoundError:
        unprocessed_nonattributable_payments = []
    for payment_file in unprocessed_nonattributable_payments:
        process_payment(payment_file, valuation, price, attributable=False)


if __name__ == "__main__":
    main()
