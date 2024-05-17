#!/usr/bin/env python

import csv
from collections import defaultdict
from decimal import Decimal, getcontext
from dataclasses import astuple
import re
import os
import subprocess
from .models import (
    Advance, Attribution, Debt, Payment, ItemizedPayment, Transaction
)
from .parsing import parse_percentage, serialize_proportion
from .git import get_git_revision_short_hash
from .accounting_utils import (
    get_rounding_difference, correct_rounding_error,
    assert_attributions_normalized
)
from .constants import (
    ABE_ROOT, PAYMENTS_DIR, PAYOUTS_DIR, TRANSACTIONS_FILE, DEBTS_FILE,
    ADVANCES_FILE, NONATTRIBUTABLE_PAYMENTS_DIR, UNPAYABLE_CONTRIBUTORS_FILE,
    ITEMIZED_PAYMENTS_FILE, PRICE_FILE, VALUATION_FILE, ATTRIBUTIONS_FILE,
    INSTRUMENTS_FILE
)


ACCOUNTING_ZERO = Decimal("0.01")

# TODO standardize the parsing from text into python objects
# e.g. Decimal and DateTime

def read_payment(payment_file, attributable=True):
    """
    Reads a payment file and uses the contents to create a Payment object.
    """
    payments_dir = (
        PAYMENTS_DIR if attributable else NONATTRIBUTABLE_PAYMENTS_DIR
    )
    with open(os.path.join(payments_dir, payment_file)) as f:
        for row in csv.reader(f, skipinitialspace=True):
            name, _email, amount, _date = row
            amount = re.sub("[^0-9.]", "", amount)
            return Payment(name, Decimal(amount), attributable, payment_file)


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


def read_attributions(attributions_filename, validate=True):
    attributions = {}
    attributions_file = os.path.join(ABE_ROOT, attributions_filename)
    with open(attributions_file) as f:
        for row in csv.reader(f):
            if row and row[0].strip():
                email, percentage = row
                email = email.strip()
                attributions[email] = parse_percentage(percentage)
    if validate:
        assert_attributions_normalized(attributions)
    return attributions


def get_all_payments():
    """
    Reads payment files and returns all existing payment objects.
    """
    try:
        payments = [
            read_payment(f, attributable=True)
        for f in os.listdir(PAYMENTS_DIR)
        if not os.path.isdir(os.path.join(PAYMENTS_DIR, f))
        ]
    except FileNotFoundError:
        payments = []
    try:
        payments += [
            read_payment(f, attributable=False)
            for f in os.listdir(NONATTRIBUTABLE_PAYMENTS_DIR)
            if not os.path.isdir(os.path.join(NONATTRIBUTABLE_PAYMENTS_DIR, f))
        ]
    except FileNotFoundError:
        pass
    return payments


def find_unprocessed_payments():
    """
    1. Read the transactions file to find out which payments are already
       recorded as transactions
    2. Read the payments folder to get all payments, as Payment objects
    3. Return those which haven't been recorded in a transaction

    Return type: list of Payment objects
    """
    recorded_payments = set()
    try:
        with open(TRANSACTIONS_FILE) as f:
            for (
                _email,
                _amount,
                payment_file,
                _commit_hash,
                _created_at,
            ) in csv.reader(f):
                recorded_payments.add(payment_file)
    except FileNotFoundError:
        pass
    all_payments = get_all_payments()
    return [p for p in all_payments if p.file not in recorded_payments]


def generate_transactions(amount, attributions, payment_file, commit_hash):
    """
    Generate transactions reflecting the amount owed to each contributor from
    a fresh payment amount -- one transaction per attributable contributor.
    """
    assert amount > 0
    assert attributions
    transactions = []
    for email, amount_owed in get_amounts_owed(amount, attributions):
        t = Transaction(email, amount_owed, payment_file, commit_hash)
        transactions.append(t)
    return transactions


def get_existing_itemized_payments():
    """
    Reads itemized payment files and returns all itemized payment objects.
    """
    itemized_payments = []
    try:
        with open(ITEMIZED_PAYMENTS_FILE) as f:
            for (
                email,
                fee_amount,
                project_amount,
                attributable,
                payment_file,
            ) in csv.reader(f):
                itemized_payment = ItemizedPayment(
                    email,
                    Decimal(fee_amount),
                    Decimal(project_amount),
                    attributable,
                    payment_file,
                )
                itemized_payments.append(itemized_payment)
    except FileNotFoundError:
        itemized_payments = []
    return itemized_payments


def total_amount_paid_to_project(for_email, new_itemized_payments):
    """
    Calculates the sum of a single user's attributable payments (minus
    fees paid towards instruments) for determining how much the user
    has invested in the project so far. Non-attributable payments do
    not count towards investment.
    """
    all_itemized_payments = (
        get_existing_itemized_payments() + new_itemized_payments
    )
    return sum(
        p.project_amount
        for p in all_itemized_payments
        if p.attributable and p.email == for_email
    )


def calculate_incoming_investment(payment, price, new_itemized_payments):
    """
    If the payment brings the aggregate amount paid by the payee
    above the price, then that excess is treated as investment.
    """
    total_payments = total_amount_paid_to_project(
        payment.email, new_itemized_payments
    )
    previous_total = total_payments - payment.amount  # fees already deducted
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


def normalize(attributions):
    total_share = sum(share for _, share in attributions.items())
    target_proportion = Decimal("1") / total_share
    for email in attributions:
        attributions[email] *= target_proportion


def write_attributions(attributions):
    # don't write attributions if they aren't normalized
    assert_attributions_normalized(attributions)
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
    with open(TRANSACTIONS_FILE, 'a') as f:
        writer = csv.writer(f)
        for row in transactions:
            writer.writerow(astuple(row))


def write_append_itemized_payments(itemized_payments):
    with open(ITEMIZED_PAYMENTS_FILE, 'a') as f:
        writer = csv.writer(f)
        for row in itemized_payments:
            writer.writerow(astuple(row))


def write_append_advances(advances):
    with open(ADVANCES_FILE, 'a') as f:
        writer = csv.writer(f)
        for row in advances:
            writer.writerow(astuple(row))


def write_valuation(valuation):
    rounded_valuation = f"{valuation:.2f}"
    with open(VALUATION_FILE, 'w') as f:
        writer = csv.writer(f)
        writer.writerow((rounded_valuation,))


def dilute_attributions(incoming_attribution, attributions):
    """
    Incorporate a fresh attributive share by diluting existing attributions,
    and correcting any rounding error that may arise from this.

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

    correct_rounding_error(attributions, incoming_attribution)


def inflate_valuation(valuation, amount):
    """
    Determine the posterior valuation as the fresh investment amount
    added to the prior valuation.
    """
    return valuation + amount


def read_debts():
    debts = []
    try:
        with open(DEBTS_FILE) as f:
            for (
                email,
                amount,
                amount_paid,
                payment_file,
                commit_hash,
                created_at,
            ) in csv.reader(f):
                debts.append(Debt(email, Decimal(amount), Decimal(amount_paid), payment_file, commit_hash, created_at))
    except FileNotFoundError:
        pass

    return debts


def read_advances(attributions):
    advances = defaultdict(list)
    try:
        with open(ADVANCES_FILE) as f:
            for (
                email,
                amount,
                payment_file,
                commit_hash,
                created_at,
            ) in csv.reader(f):
                if email in attributions:
                    advances[email].append(Advance(email, Decimal(amount), payment_file, commit_hash, created_at))
    except FileNotFoundError:
        pass

    return advances


def get_sum_of_advances_by_contributor(attributions):
    """
    Sum all Advance objects for each contributor to get the total amount
    that they currently have in advances and have not yet drawn down.
    Return a dictionary with the contributor's email as the key and the
    their advance amount as the value.
    """
    all_advances = read_advances(attributions)
    advance_totals = {email: sum(a.amount for a in advances)
                      for email, advances
                      in all_advances.items()}
    return advance_totals


def get_payable_debts(unpayable_contributors, attributions):
    debts = read_debts()
    debts = [d for d in debts
             if not d.is_fulfilled()
             and d.email in attributions
             and d.email not in unpayable_contributors]
    return debts


def pay_debts(payable_debts, payment):
    """
    Go through debts in chronological order, and pay each as much as possible,
    stopping when either the money runs out, or there are no further debts.
    Returns the updated debts reflecting fresh payments to be made this time,
    and transactions representing those fresh payments.
    """
    updated_debts = []
    transactions = []
    available_amount = payment.amount
    for debt in sorted(payable_debts, key=lambda x: x.created_at):
        payable_amount = min(available_amount, debt.amount_remaining())
        if payable_amount < ACCOUNTING_ZERO:
            break
        debt.amount_paid += payable_amount
        available_amount -= payable_amount
        transaction = Transaction(debt.email, payable_amount, payment.file, debt.commit_hash)
        transactions.append(transaction)
        updated_debts.append(debt)

    return updated_debts, transactions


def get_unpayable_contributors():
    """
    Read the unpayable_contributors file to get the list of contributors who
    are unpayable.
    """
    contributors = []
    try:
        with open(UNPAYABLE_CONTRIBUTORS_FILE) as f:
            for contributor in f:
                contributor = contributor.strip()
                if contributor:
                    contributors.append(contributor)
    except FileNotFoundError:
        pass
    return contributors


def create_debts(amounts_owed, unpayable_contributors, payment_file):
    """
    Create fresh debts (to unpayable contributors).
    """
    amounts_unpayable = {email: amount
                         for email, amount in amounts_owed.items()
                         if email in unpayable_contributors}
    debts = []
    commit_hash = get_git_revision_short_hash()
    for email, amount in amounts_unpayable.items():
        debt = Debt(email, amount, payment_file=payment_file, commit_hash=commit_hash)
        debts.append(debt)

    return debts


def write_debts(processed_debts):
    """
    1. Build a hash of all the processed debts, generating an id for each
       (based on email and payment file).
    2. read the existing debts file, row by row.
    3. if the debt in the row is in the "processed" hash, then write the
       processed version instead of the input version and remove it from the
       hash, otherwise write the input version.
    4. write the debts that remain in the processed hash.
    """
    existing_debts = read_debts()
    processed_debts_hash = {debt.key(): debt for debt in processed_debts}
    with open(DEBTS_FILE, 'w') as f:
        writer = csv.writer(f)
        for existing_debt in existing_debts:
            # if the existing debt has been processed, write the processed version
            # otherwise re-write the existing version
            if processed_debt := processed_debts_hash.get(existing_debt.key()):
                writer.writerow(astuple(processed_debt))
                del processed_debts_hash[processed_debt.key()]
            else:
                writer.writerow(astuple(existing_debt))
        for debt in processed_debts_hash.values():
            writer.writerow(astuple(debt))


def renormalize(attributions, excluded_contributors):
    target_proportion = 1 / (1 - sum(attributions[email] for email in excluded_contributors))
    remainder_attributions = {}
    for email in attributions:
        # renormalize to reflect dilution
        remainder_attributions[email] = attributions[email] * target_proportion
    return remainder_attributions


def get_amounts_owed(total_amount, attributions):
    return {email: share * total_amount
            for email, share in attributions.items()}


def redistribute_pot(redistribution_pot, attributions, unpayable_contributors, payment_file, amounts_payable):
    """
    Redistribute the pot of remaining money over all payable contributors, according to attributions
    share (normalized to 100%). Create advances for those amounts (because they are in excess
    of the amount owed to each contributor from the original payment) and add the amounts to the
    amounts_payable dictionary to keep track of the full amount we are about to pay everyone.
    """
    fresh_advances = []
    payable_attributions = {email: share for email, share in attributions.items() if email not in unpayable_contributors}
    normalize(payable_attributions)
    for email, share in payable_attributions.items():
        advance_amount = redistribution_pot * share
        fresh_advances.append(Advance(email=email,
                                      amount=advance_amount,
                                      payment_file=payment_file,
                                      commit_hash=get_git_revision_short_hash()))
        amounts_payable[email] += advance_amount

    return fresh_advances


def distribute_payment(payment, attributions):
    """
    Generate transactions to contributors from a (new) payment.

    We consult the attribution file and determine how much is owed
    to each contributor based on the current percentages, generating a
    fresh entry in the transactions file for each contributor.
    """

    # 1. check payable outstanding debts
    # 2. pay them off in chronological order (maybe partially)
    # 3. (if leftover) identify unpayable people in the relevant attributions file
    # 4. record debt for each of them according to their attribution
    commit_hash = get_git_revision_short_hash()
    unpayable_contributors = get_unpayable_contributors()
    payable_debts = get_payable_debts(unpayable_contributors, attributions)
    updated_debts, debt_transactions = pay_debts(payable_debts, payment)
    # The "available" amount is what is left over after paying off debts
    available_amount = payment.amount - sum(t.amount for t in debt_transactions)

    fresh_debts = []
    equity_transactions = []
    negative_advances = []
    fresh_advances = []
    if available_amount > ACCOUNTING_ZERO:
        amounts_owed = get_amounts_owed(available_amount, attributions)
        fresh_debts = create_debts(amounts_owed,
                                   unpayable_contributors,
                                   payment.file)
        redistribution_pot = sum(d.amount for d in fresh_debts)

        # just retain payable people and their amounts owed
        amounts_payable = {email: amount
                           for email, amount in amounts_owed.items()
                           if email not in unpayable_contributors}

        # use the amount owed to each contributor to draw down any advances
        # they may already have and then decrement their amount payable accordingly
        advance_totals = get_sum_of_advances_by_contributor(attributions)
        for email, advance_total in advance_totals.items():
            amount_payable = amounts_payable.get(email, 0)
            drawdown_amount = min(advance_total, amount_payable)
            if drawdown_amount > ACCOUNTING_ZERO:
                negative_advance = Advance(email=email,
                                           amount=-drawdown_amount, # note minus sign
                                           payment_file=payment.file,
                                           commit_hash=commit_hash)
                negative_advances.append(negative_advance)
                amounts_payable[email] -= drawdown_amount

        # note that these are drawn down amounts and therefore have negative amounts
        # and that's why we take the absolute value here
        redistribution_pot += sum(abs(a.amount) for a in negative_advances)

        # redistribute the pot over all payable contributors - produce fresh advances and add to amounts payable
        if redistribution_pot > ACCOUNTING_ZERO:
            fresh_advances = redistribute_pot(redistribution_pot,
                                              attributions,
                                              unpayable_contributors,
                                              payment.file,
                                              amounts_payable)

        for email, amount in amounts_payable.items():
            new_equity_transaction = Transaction(email=email,
                                                 amount=amount,
                                                 payment_file=payment.file,
                                                 commit_hash=commit_hash)
            equity_transactions.append(new_equity_transaction)

    debts = updated_debts + fresh_debts
    transactions = equity_transactions + debt_transactions
    advances = negative_advances + fresh_advances

    return debts, transactions, advances


def handle_investment(
    payment, new_itemized_payments, attributions, price, prior_valuation
):
    """
    For "attributable" payments (the default), we determine
    if some portion of it counts as an investment in the project. If it does,
    then the valuation is inflated by the investment amount, and the payer is
    attributed a share commensurate with their investment, diluting the
    attributions.
    """
    incoming_investment = calculate_incoming_investment(
        payment, price, new_itemized_payments
    )
    # inflate valuation by the amount of the fresh investment
    posterior_valuation = inflate_valuation(
        prior_valuation, incoming_investment
    )
    incoming_attribution = calculate_incoming_attribution(
        payment.email, incoming_investment, posterior_valuation
    )
    if incoming_attribution and incoming_attribution.share > ACCOUNTING_ZERO:
        dilute_attributions(incoming_attribution, attributions)
    return posterior_valuation


def _create_itemized_payment(payment, fee_amount):
    return ItemizedPayment(
        payment.email,
        fee_amount,
        payment.amount,  # already has fees deducted
        payment.attributable,
        payment.file,
    )


def process_payments(instruments, attributions):
    """
    Process new payments by paying out instruments and then, from the amount
    left over, paying out attributions.
    Returns all newly created transactions and the updated valuation amount
    after all of the new payments have been processed.
    """
    price = read_price()
    valuation = read_valuation()
    new_debts = []
    new_advances = []
    new_transactions = []
    new_itemized_payments = []
    unprocessed_payments = find_unprocessed_payments()
    for payment in unprocessed_payments:
        # first, process instruments (i.e. pay fees)
        debts, transactions, advances = distribute_payment(payment, instruments)
        new_transactions += transactions
        new_debts += debts
        new_advances += advances
        fees_paid_out = sum(t.amount for t in transactions)
        # deduct the amount paid out to instruments before
        # processing it for attributions
        payment.amount -= fees_paid_out
        new_itemized_payments.append(
            _create_itemized_payment(payment, fees_paid_out)
        )
        # next, process attributions - using the amount owed to the project
        # (which is the amount leftover after paying instruments/fees)
        if payment.amount > ACCOUNTING_ZERO:
            debts, transactions, advances = distribute_payment(payment, attributions)
            new_transactions += transactions
            new_debts += debts
            new_advances += advances
        if payment.attributable:
            valuation = handle_investment(
                payment, new_itemized_payments, attributions, price, valuation
            )
    return new_debts, new_transactions, valuation, new_itemized_payments, new_advances


def process_payments_and_record_updates():
    """
    Allocate incoming payments to contributors according to the instruments
    and attributions files. Record updated transactions, valuation, and
    renormalized attributions only after all payments have been processed.
    """
    instruments = read_attributions(INSTRUMENTS_FILE, validate=False)
    attributions = read_attributions(ATTRIBUTIONS_FILE)

    (
        debts,
        transactions,
        posterior_valuation,
        new_itemized_payments,
        advances,
    ) = process_payments(instruments, attributions)

    # we only write the changes to disk at the end
    # so that if any errors are encountered, no
    # changes are made.
    write_debts(debts)
    write_append_transactions(transactions)
    write_attributions(attributions)
    write_valuation(posterior_valuation)
    write_append_itemized_payments(new_itemized_payments)
    write_append_advances(advances)


def main():
    # Set the decimal precision explicitly so that we can
    # be sure that it is the same regardless of where
    # it is run, to avoid any possible accounting errors
    getcontext().prec = 10

    process_payments_and_record_updates()


if __name__ == "__main__":
    main()
