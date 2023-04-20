#!/usr/bin/env python

import csv
from decimal import Decimal, getcontext
from dataclasses import astuple
import re
import os
import subprocess
from .models import Payment, Transaction

ABE_ROOT = 'abe'
PAYMENTS_DIR = os.path.join(ABE_ROOT, 'payments')
NONATTRIBUTABLE_PAYMENTS_DIR = os.path.join(
    ABE_ROOT, 'payments', 'nonattributable'
)
TRANSACTIONS_FILE = os.path.join(ABE_ROOT, 'transactions.txt')
PRICE_FILE = os.path.join(ABE_ROOT, 'price.txt')
VALUATION_FILE = os.path.join(ABE_ROOT, 'valuation.txt')
ATTRIBUTIONS_FILE = os.path.join(ABE_ROOT, 'attributions.txt')

ROUNDING_TOLERANCE = Decimal("0.000001")


def parse_percentage(value):
    """
    Translates values expressed in percentage format (75.234) into
    their decimal equivalents (0.75234). This effectively divides
    the value by 100 without losing precision.
    """
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
    """
    Translates values expressed in decimal format (0.75234) into
    their percentage equivalents (75.234). This effectively multiplies
    the value by 100 without losing precision.
    """
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
    payments_dir = (
        PAYMENTS_DIR if attributable else NONATTRIBUTABLE_PAYMENTS_DIR
    )
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
    payments_dir = (
        PAYMENTS_DIR if attributable else NONATTRIBUTABLE_PAYMENTS_DIR
    )
    return {
        f
        for f in os.listdir(payments_dir)
        if not os.path.isdir(os.path.join(payments_dir, f))
    }


def find_unprocessed_payment_files(attributable=True):
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
    """
    Generate transactions reflecting the amount owed to each contributor from
    a fresh payment amount -- one transaction per attributable contributor.
    """
    assert amount > 0
    assert attributions
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


def calculate_incoming_investment(payment, price):
    """
    If the payment brings the aggregate amount paid by the payee
    above the price, then that excess is treated as investment.
    """
    total_payments = total_amount_paid(payment.email, attributable=True)
    previous_total = total_payments - payment.amount
    # how much of the incoming amount goes towards investment?
    incoming_investment = total_payments - max(price, previous_total)
    return max(0, incoming_investment)


def calculate_incoming_attribution(email,
                                   incoming_investment,
                                   posterior_valuation):
    """
    If there is an incoming investment, find out what proportion it
    represents of the overall (posterior) valuation of the project.
    """
    if incoming_investment > 0:
        share = incoming_investment / posterior_valuation
        return email, share
    else:
        return None


def get_rounding_difference(attributions):
    """
    Get the difference of the total of the attributions from 1, which is
    expected to occur due to finite precision. If the difference exceeds the
    expected error tolerance, an error is signaled.
    """
    total = sum(attributions.values())
    difference = total - Decimal("1")
    assert abs(difference) <= ROUNDING_TOLERANCE
    return difference


def renormalize(attributions, incoming_attribution):
    """
    The incoming attribution is determined as a proportion of the total
    posterior valuation.  As the existing attributions total to 1 and don't
    account for it, they must be proportionately scaled so that their new total
    added to the incoming attribution once again totals to one, i.e. is
    "renormalized."  This effectively dilutes the attributions by the magnitude
    of the incoming attribution.
    """
    incoming_email, incoming_share = incoming_attribution
    target_proportion = Decimal("1") - incoming_share
    for email in attributions:
        # renormalize to reflect dilution
        attributions[email] *= target_proportion
    # add incoming share to existing investor or record new investor
    attributions[incoming_email] = (
        attributions.get(incoming_email, 0) + incoming_share
    )


def correct_rounding_error(attributions, incoming_email):
    """Due to finite precision, the Decimal module will round up or down
    on the last decimal place. This could result in the aggregate value not
    quite totaling to 1. This corrects that total by either adding or
    subtracting the difference from the incoming attribution (by convention).
    """
    difference = get_rounding_difference(attributions)
    attributions[incoming_email] -= difference


def write_attributions(attributions):
    # don't write attributions if they aren't normalized
    assert sum(attributions.values()) == Decimal("1")
    # format for output as percentages
    attributions = [
        (email, serialize_proportion(share))
        for email, share in attributions.items()
    ]
    with open(ATTRIBUTIONS_FILE, 'w') as f:
        writer = csv.writer(f)
        for row in attributions:
            writer.writerow(row)


def write_transactions(transactions):
    with open(TRANSACTIONS_FILE, 'a') as f:
        writer = csv.writer(f)
        for row in transactions:
            writer.writerow(astuple(row))


def write_valuation(valuation):
    with open(VALUATION_FILE, 'w') as f:
        writer = csv.writer(f)
        writer.writerow((valuation,))


def dilute_attributions(incoming_attribution, attributions):
    """
    Incorporate a fresh attributive share by diluting existing attributions,
    and correcting any rounding error that may arise from this.
    """
    renormalize(attributions, incoming_attribution)
    correct_rounding_error(attributions, incoming_attribution[0])
    write_attributions(attributions)


def inflate_valuation(valuation, amount):
    """
    Determine the posterior valuation as the fresh investment amount
    added to the prior valuation.
    """
    new_valuation = valuation + amount
    write_valuation(new_valuation)
    return new_valuation


def get_git_revision_short_hash() -> str:
    """From https://stackoverflow.com/a/21901260"""
    return (
        subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'])
        .decode('ascii')
        .strip()
    )


def distribute_payment(payment, attributions):
    """
    Generate transactions to contributors from a (new) payment.

    We consult the attribution file and determine how much is owed
    to each contributor based on the current percentages, generating a
    fresh entry in the transactions file for each contributor.
    """
    commit_hash = get_git_revision_short_hash()

    # figure out how much each person in the attributions file is owed from
    # this payment, generating a transaction for each stakeholder.
    transactions = generate_transactions(
        payment.amount, attributions, payment.file, commit_hash
    )
    write_transactions(transactions)


def handle_investment(payment, attributions, price, prior_valuation):
    """
    For "attributable" payments (the default), we determine
    if some portion of it counts as an investment in the project. If it does,
    then the valuation is inflated by the investment amount, and the payer is
    attributed a share commensurate with their investment, diluting the
    attributions.
    """
    incoming_investment = calculate_incoming_investment(
        payment, price
    )
    # inflate valuation by the amount of the fresh investment
    posterior_valuation = inflate_valuation(prior_valuation, incoming_investment)
    incoming_attribution = calculate_incoming_attribution(
        payment.email, incoming_investment, posterior_valuation
    )
    if incoming_attribution:
        dilute_attributions(incoming_attribution, attributions)


def _get_unprocessed_payment_files(attributable=True):
    try:
        unprocessed_payments = find_unprocessed_payment_files(attributable)
    except FileNotFoundError:
        unprocessed_payments = []
    print(unprocessed_payments)
    return unprocessed_payments


def process_new_attributable_payments(attributions):
    """
    Process payments that are "attributable" (i.e. the default).

    For such payments, some portion of it may count as an investment.
    Investments (a) inflate the valuation and (b) dilute attributions.
    """
    price = read_price()
    valuation = read_valuation()
    unprocessed_payments = _get_unprocessed_payment_files(attributable=True)
    for payment_file in unprocessed_payments:
        print(payment_file)
        payment = read_payment(payment_file, attributable=True)
        distribute_payment(payment, attributions)
        handle_investment(payment, attributions, price, valuation)


def process_new_nonattributable_payments(attributions):
    """
    Process payments that are "nonattributable."

    For nonattributable payments, the entire amount is treated as compensation
    and no component of it counts towards investment. This is typically the
    case for attributive revenue, that is, revenue from downstream projects
    that recognize the present project in their attributions.

    Note that nonattributable payments do not inflate the valuation nor do they
    dilute attributions.
    """
    unprocessed_payments = _get_unprocessed_payment_files(attributable=False)
    for payment_file in unprocessed_payments:
        print(payment_file)
        payment = read_payment(payment_file, attributable=False)
        distribute_payment(payment, attributions)


def process_new_payments():
    attributions = read_attributions()
    # this does not change attributions
    process_new_nonattributable_payments(attributions)
    process_new_attributable_payments(attributions)


def main():
    # Set the decimal precision explicitly so that we can
    # be sure that it is the same regardless of where
    # it is run, to avoid any possible accounting errors
    getcontext().prec = 10

    process_new_payments()


if __name__ == "__main__":
    main()
