#!/usr/bin/env python

import csv
from decimal import Decimal, getcontext
from dataclasses import astuple
import re
import os
import subprocess
from .models import Attribution, Payment, Transaction

ABE_ROOT = 'abe'
PAYMENTS_DIR = os.path.join(ABE_ROOT, 'payments')
NONATTRIBUTABLE_PAYMENTS_DIR = os.path.join(
    ABE_ROOT, 'payments', 'nonattributable'
)
TRANSACTIONS_FILE = 'transactions.txt'
PRICE_FILE = 'price.txt'
VALUATION_FILE = 'valuation.txt'
ATTRIBUTIONS_FILE = 'attributions.txt'
INSTRUMENTS_FILE = 'instruments.txt'

ROUNDING_TOLERANCE = Decimal("0.000001")
ACCOUNTING_ZERO = Decimal("0.01")


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
        value = value + "00"
    else:
        value = value + ".00"
    value = re.sub(
        r"(?P<pre>\d)\.(?P<post>\d{2})(?P<rest>\d*)",
        # match a number followed by a decimal point
        # followed by at least two digits
        r"\g<pre>\g<post>.\g<rest>",
        # move the decimal point two places to the right
        value,
    )
    # strip leading insignificant zeroes
    value = value.lstrip("0")
    # ensure there's a single leading zero if it is
    # a decimal value less than 1
    value = re.sub(r"^\.", r"0.", value)
    if "." in value:
        # strip trailing insignificant zeroes
        value = value.rstrip("0")
        # remove decimal point if whole number
        value = re.sub(r"\.$", r"", value)
    return value


def read_payment(payment_file, attributable=True):
    payments_dir = (
        PAYMENTS_DIR if attributable else NONATTRIBUTABLE_PAYMENTS_DIR
    )
    with open(os.path.join(payments_dir, payment_file)) as f:
        for row in csv.reader(f, skipinitialspace=True):
            name, _email, amount, _date = row
            amount = re.sub("[^0-9.]", "", amount)
            return Payment(name, Decimal(amount), attributable, payment_file)


def read_price():
    price_file = os.path.join(ABE_ROOT, PRICE_FILE)
    with open(price_file) as f:
        price = f.readline()
        price = Decimal(re.sub("[^0-9.]", "", price))
        return price


# note that commas are used as a decimal separator in some languages
# (e.g. Spain Spanish), so that would need to be handled at some point
def read_valuation():
    valuation_file = os.path.join(ABE_ROOT, VALUATION_FILE)
    with open(valuation_file) as f:
        valuation = f.readline()
        valuation = Decimal(re.sub("[^0-9.]", "", valuation))
        return valuation


def read_attributions(attributions_filename):
    attributions = {}
    attributions_file = os.path.join(ABE_ROOT, attributions_filename)
    with open(attributions_file) as f:
        for row in csv.reader(f):
            email, percentage = row
            attributions[email] = parse_percentage(percentage)
    assert _get_attributions_total(attributions) == Decimal("1")
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
    transactions_file = os.path.join(ABE_ROOT, TRANSACTIONS_FILE)
    with open(transactions_file) as f:
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
    for email, share in attributions.items():
        t = Transaction(email, amount * share, payment_file, commit_hash)
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


def calculate_incoming_attribution(
    email, incoming_investment, posterior_valuation
):
    """
    If there is an incoming investment, find out what proportion it
    represents of the overall (posterior) valuation of the project.
    """
    if incoming_investment > 0:
        share = incoming_investment / posterior_valuation
        return Attribution(email, share)
    else:
        return None


def _get_attributions_total(attributions):
    return sum(attributions.values())


def get_rounding_difference(attributions):
    """
    Get the difference of the total of the attributions from 1, which is
    expected to occur due to finite precision. If the difference exceeds the
    expected error tolerance, an error is signaled.
    """
    total = _get_attributions_total(attributions)
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
    target_proportion = Decimal("1") - incoming_attribution.share
    for email in attributions:
        # renormalize to reflect dilution
        attributions[email] *= target_proportion
    # add incoming share to existing investor or record new investor
    existing_attribution = attributions.get(incoming_attribution.email, None)
    attributions[incoming_attribution.email] = (
        existing_attribution if existing_attribution else 0
    ) + incoming_attribution.share


def correct_rounding_error(attributions, incoming_attribution):
    """Due to finite precision, the Decimal module will round up or down
    on the last decimal place. This could result in the aggregate value not
    quite totaling to 1. This corrects that total by either adding or
    subtracting the difference from the incoming attribution (by convention).
    """
    difference = get_rounding_difference(attributions)
    attributions[incoming_attribution.email] -= difference


def write_attributions(attributions):
    # don't write attributions if they aren't normalized
    assert _get_attributions_total(attributions) == Decimal("1")
    # format for output as percentages
    attributions = [
        (email, serialize_proportion(share))
        for email, share in attributions.items()
    ]
    attributions_file = os.path.join(ABE_ROOT, ATTRIBUTIONS_FILE)
    with open(attributions_file, 'w') as f:
        writer = csv.writer(f)
        for row in attributions:
            writer.writerow(row)


def write_append_transactions(transactions):
    transactions_file = os.path.join(ABE_ROOT, TRANSACTIONS_FILE)
    with open(transactions_file, 'a') as f:
        writer = csv.writer(f)
        for row in transactions:
            writer.writerow(astuple(row))


def write_valuation(valuation):
    rounded_valuation = f"{valuation:.2f}"
    valuation_file = os.path.join(ABE_ROOT, VALUATION_FILE)
    with open(valuation_file, 'w') as f:
        writer = csv.writer(f)
        writer.writerow((rounded_valuation,))


def dilute_attributions(incoming_attribution, attributions):
    """
    Incorporate a fresh attributive share by diluting existing attributions,
    and correcting any rounding error that may arise from this.
    """
    renormalize(attributions, incoming_attribution)
    correct_rounding_error(attributions, incoming_attribution)


def inflate_valuation(valuation, incoming_investment, attributions):
    """
    Determine the posterior valuation as the fresh investment amount
    added to the prior valuation, after retaining only that component
    of the incoming investment that is retained in the current project.
    """
    dilutable_shares = [a.share for a in attributions.values() if a.dilutable]
    dilutable_proportion = sum(dilutable_shares)
    amount = incoming_investment * dilutable_proportion
    return valuation + amount


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
    return transactions


def handle_investment(payment, attributions, price, prior_valuation):
    """
    For "attributable" payments (the default), we determine
    if some portion of it counts as an investment in the project. If it does,
    then the valuation is inflated by the investment amount, and the payer is
    attributed a share commensurate with their investment, diluting the
    attributions.
    """
    incoming_investment = calculate_incoming_investment(payment, price)
    # inflate valuation by the amount of the fresh investment
    posterior_valuation = inflate_valuation(
        prior_valuation, incoming_investment, attributions,
    )
    incoming_attribution = calculate_incoming_attribution(
        payment.email, incoming_investment, posterior_valuation
    )
    if incoming_attribution:
        dilute_attributions(incoming_attribution, attributions)
    return posterior_valuation


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
    unprocessed_payments = _get_unprocessed_payment_files(attributable=True)
    transactions = []
    for payment_file in unprocessed_payments:
        print(payment_file)
        payment = read_payment(payment_file, attributable=True)
        transactions += distribute_payment(payment, attributions)
        valuation = handle_investment(payment, attributions, price, valuation)
    return transactions, valuation


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


def _process_payments(instruments, attributions, attributable):
    price = read_price()
    valuation = read_valuation()
    new_transactions = []
    unprocessed_payments = _get_unprocessed_payment_files(attributable)
    for payment_file in unprocessed_payments:
        payment = read_payment(payment_file, attributable)
        transactions = distribute_payment(payment, instruments)
        new_transactions += transactions
        amount_paid_out = sum(t.amount for t in transactions)
        payment.amount -= amount_paid_out
        if payment.amount > ACCOUNTING_ZERO:
            new_transactions += distribute_payment(payment, attributions)
        if attributable:
            valuation = handle_investment(payment, attributions, price, valuation)
    return new_transactions, valuation


def process_new_payments(attributions):

    attributions = read_attributions(ATTRIBUTIONS_FILE)
    instruments = read_attributions(INSTRUMENTS_FILE)

    new_transactions = []

    transactions, _ = _process_payments(instruments, attributions, attributable=False)
    new_transactions += transactions
    transactions, posterior_valuation = _process_payments(instruments, attributions, attributable=True)
    new_transactions += transactions

    # we only write the changes to disk at the end
    # so that if any errors are encountered, no
    # changes are made.
    write_append_transactions(new_transactions)
    write_attributions(attributions)
    write_valuation(posterior_valuation)


def main():
    # Set the decimal precision explicitly so that we can
    # be sure that it is the same regardless of where
    # it is run, to avoid any possible accounting errors
    getcontext().prec = 10

    process_new_payments()


if __name__ == "__main__":
    main()
