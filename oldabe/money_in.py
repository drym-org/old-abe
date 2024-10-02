#!/usr/bin/env python

import csv
import dataclasses
import re
from dataclasses import astuple, replace
from decimal import Decimal, getcontext
from itertools import accumulate
from typing import Iterable, List, Set, Tuple

from .accounting_utils import (
    assert_attributions_normalized,
    correct_rounding_error,
)
from .constants import (
    ACCOUNTING_ZERO,
    ATTRIBUTIONS_FILE,
    DEBTS_FILE,
    PRICE_FILE,
    VALUATION_FILE,
)
from .distribution import Distribution
from .models import (
    Advance,
    Attribution,
    Debt,
    DebtPayment,
    ItemizedPayment,
    Payment,
    Transaction,
)
from .parsing import serialize_proportion
from .repos import (
    AdvancesRepo,
    AllPaymentsRepo,
    AttributionsRepo,
    DebtsRepo,
    InstrumentsRepo,
    ItemizedPaymentsRepo,
    TransactionsRepo,
    UnpayableContributorsRepo,
)
from .tally import Tally


def read_price() -> Decimal:
    with open(PRICE_FILE) as f:
        price = f.readline()
        price = Decimal(re.sub("[^0-9.]", "", price))
        return price


# note that commas are used as a decimal separator in some languages
# (e.g. Spain Spanish), so that would need to be handled at some point
def read_valuation() -> Decimal:
    with open(VALUATION_FILE) as f:
        valuation = f.readline()
        valuation = Decimal(re.sub("[^0-9.]", "", valuation))
        return valuation


def write_valuation(valuation):
    rounded_valuation = f"{valuation:.2f}"
    with open(VALUATION_FILE, "w") as f:
        writer = csv.writer(f)
        writer.writerow((rounded_valuation,))


def write_attributions(attributions):
    # don't write attributions if they aren't normalized
    assert_attributions_normalized(attributions)
    # format for output as percentages
    attributions = [
        (email, serialize_proportion(share))
        for email, share in attributions.items()
    ]
    with open(ATTRIBUTIONS_FILE, "w") as f:
        writer = csv.writer(f)
        for row in attributions:
            writer.writerow(row)


def write_debts(new_debts, debt_payments):
    """
    1. Build a hash of all the processed debts, generating an id for each
       (based on email and payment file).
    2. read the existing debts file, row by row.
    3. if the debt in the row is in the "processed" hash, then write the
       processed version instead of the input version and remove it from the
       hash, otherwise write the input version.
    4. write the debts that remain in the processed hash.
    """
    print(new_debts, debt_payments)
    total_debt_payments = Tally(
        (dp.debt.key(), dp.amount) for dp in debt_payments
    )
    replacement = [
        (
            dataclasses.replace(
                debt,
                amount_paid=debt.amount_paid + total_debt_payments[debt.key()],
            )
            if debt.key() in total_debt_payments
            else debt
        )
        for debt in [*DebtsRepo(), *new_debts]
    ]
    print(total_debt_payments, list(DebtsRepo()), replacement)

    with open(DEBTS_FILE, "w") as f:
        writer = csv.writer(f)
        for debt in replacement:
            writer.writerow(astuple(debt))


def pay_outstanding_debts(
    available_amount: Decimal,
    all_debts: Iterable[Debt],
    payable_contributors: Set[str],
) -> List[DebtPayment]:
    """
    Given an available amount return debt payments for as many debts as can
    be covered
    """
    payable_debts = [
        d
        for d in all_debts
        if not d.is_fulfilled() and d.email in payable_contributors
    ]

    cummulative_debt = [
        amount
        for amount in accumulate(
            (d.amount_remaining() for d in payable_debts), initial=0
        )
        if amount <= available_amount
    ]

    return [
        DebtPayment(
            debt=d,
            amount=min(d.amount_remaining(), available_amount - already_paid),
        )
        for d, already_paid in zip(payable_debts, cummulative_debt)
    ]


def create_debts(
    available_amount: Decimal,
    distribution: Distribution,
    payable_contributors: Set[str],
    payment: Payment,
):
    return [
        Debt(
            email=email,
            amount=amount,
            amount_paid=Decimal(0),
            payment_file=payment.file,
        )
        for email, amount in distribution.distribute(available_amount).items()
        if email not in payable_contributors
    ]


def distribute_payment(
    payment: Payment, distribution: Distribution
) -> Tuple[List[Debt], List[DebtPayment], List[Transaction], List[Advance]]:
    """
    Generate transactions to contributors from a (new) payment.

    We consult the attribution file and determine how much is owed
    to each contributor based on the current percentages, generating a
    fresh entry in the transactions file for each contributor.
    """

    # 1. check payable outstanding debts
    # 2. pay them off in chronological order (maybe partially)
    # 3. (if leftover) identify unpayable people in the relevant distribution file
    # 4. record debt for each of them according to their attribution

    unpayable_contributors = set(UnpayableContributorsRepo())
    payable_contributors = {
        email
        for email in distribution
        if email and email not in unpayable_contributors
    }

    #
    # Pay as many outstanding debts as possible
    #

    debt_payments = pay_outstanding_debts(
        payment.amount, DebtsRepo(), payable_contributors
    )

    # The "available" amount is what is left over after paying off debts
    available_amount = payment.amount - sum(dp.amount for dp in debt_payments)

    #
    # Create fresh debts for anyone we can't pay
    #
    # TODO: Make it clearer that some people get debts and the others get N advances (maybe zero)

    fresh_debts = create_debts(
        available_amount, distribution, payable_contributors, payment
    )

    #
    # Draw dawn contributor's existing advances first, before paying them
    #

    advance_totals = Tally((a.email, a.amount) for a in AdvancesRepo())

    negative_advances = [
        Advance(
            email=email,
            amount=-min(
                payable_amount, advance_totals[email]
            ),  # Note the negative sign
            payment_file=payment.file,
        )
        for email, payable_amount in distribution.without(
            unpayable_contributors
        )
        .distribute(available_amount)
        .items()
        if advance_totals[email] > ACCOUNTING_ZERO
    ]

    #
    # Advance payable contributors any extra money
    #

    redistribution_pot = Decimal(
        # amount we will not pay because we created debts instead
        sum(d.amount for d in fresh_debts)
        # amount we will not pay because we drew down advances instead
        # these are negative amounts, hence the abs
        + sum(abs(a.amount) for a in negative_advances)
    )

    fresh_advances = (
        [
            Advance(
                email=email,
                amount=amount,
                payment_file=payment.file,
            )
            for email, amount in distribution.without(unpayable_contributors)
            .distribute(redistribution_pot)
            .items()
        ]
        if redistribution_pot > ACCOUNTING_ZERO
        else []
    )

    #
    # Create equity transactions for the total amounts of outgoing money
    #

    negative_advance_totals = Tally(
        (a.email, a.amount) for a in negative_advances
    )
    fresh_advance_totals = Tally((a.email, a.amount) for a in fresh_advances)
    debt_payments_totals = Tally(
        (dp.debt.email, dp.amount) for dp in debt_payments
    )

    transactions = [
        Transaction(
            email=email,
            payment_file=payment.file,
            amount=(
                # what you would normally get
                equity
                # minus amount drawn from your advances
                - abs(negative_advance_totals[email])
                # plus new advances from the pot
                + fresh_advance_totals[email]
                # plus any payments for old debts
                + debt_payments_totals[email]
            ),
        )
        for email, equity in distribution.distribute(available_amount).items()
        if email in payable_contributors
    ]

    processed_debts = fresh_debts
    advances = negative_advances + fresh_advances

    return processed_debts, debt_payments, transactions, advances


def calculate_incoming_investment(payment, price, new_itemized_payments):
    """
    If the payment brings the aggregate amount paid by the payee
    above the price, then that excess is treated as investment.
    """
    total_attributable_payments = sum(
        p.project_amount
        for p in [*ItemizedPaymentsRepo(), *new_itemized_payments]
        if p.attributable and p.email == payment.email
    )

    incoming_investment = min(
        total_attributable_payments - price, payment.amount
    )

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
    posterior_valuation = prior_valuation + incoming_investment

    incoming_attribution = calculate_incoming_attribution(
        payment.email, incoming_investment, posterior_valuation
    )
    if incoming_attribution and incoming_attribution.share > ACCOUNTING_ZERO:
        dilute_attributions(incoming_attribution, attributions)
    return posterior_valuation


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
    new_debt_payments = []
    new_advances = []
    new_transactions = []
    new_itemized_payments = []

    processed_payment_files = {t.payment_file for t in TransactionsRepo()}
    unprocessed_payments = [
        p for p in AllPaymentsRepo() if p.file not in processed_payment_files
    ]

    for payment in unprocessed_payments:
        # first, process instruments (i.e. pay fees)
        debts, debt_payments, transactions, advances = distribute_payment(
            payment,
            Distribution(
                # The missing percentage in the instruments file
                # should not be distributed to anyone (shareholder: None)
                # TODO: Move to process_payments_and_record_updates
                {**instruments, None: Decimal(1) - sum(instruments.values())}
            ),
        )
        new_transactions += transactions
        new_debts += debts
        new_debt_payments += debt_payments
        new_advances += advances
        fees_paid_out = sum(t.amount for t in transactions)
        # deduct the amount paid out to instruments before
        # processing it for attributions
        payment.amount -= fees_paid_out
        new_itemized_payments.append(
            ItemizedPayment(
                payment.email,
                fees_paid_out,
                payment.amount,  # already has fees deducted
                payment.attributable,
                payment.file,
            )
        )
        # next, process attributions - using the amount owed to the project
        # (which is the amount leftover after paying instruments/fees)
        if payment.amount > ACCOUNTING_ZERO:
            debts, debt_payments, transactions, advances = distribute_payment(
                payment, Distribution(attributions)
            )
            new_transactions += transactions
            new_debts += debts
            new_debt_payments += debt_payments
            new_advances += advances
        if payment.attributable:
            valuation = handle_investment(
                payment, new_itemized_payments, attributions, price, valuation
            )
    return (
        new_debts,
        new_debt_payments,
        new_transactions,
        valuation,
        new_itemized_payments,
        new_advances,
    )


def process_payments_and_record_updates():
    """
    Allocate incoming payments to contributors according to the instruments
    and attributions files. Record updated transactions, valuation, and
    renormalized attributions only after all payments have been processed.
    """
    instruments = {a.email: a.decimal_share for a in InstrumentsRepo()}
    attributions = {a.email: a.decimal_share for a in AttributionsRepo()}

    assert_attributions_normalized(attributions)

    (
        new_debts,
        debt_payments,
        transactions,
        posterior_valuation,
        new_itemized_payments,
        advances,
    ) = process_payments(instruments, attributions)

    # we only write the changes to disk at the end
    # so that if any errors are encountered, no
    # changes are made.
    write_debts(new_debts, debt_payments)
    TransactionsRepo().extend(transactions)
    write_attributions(attributions)
    write_valuation(posterior_valuation)
    ItemizedPaymentsRepo().extend(new_itemized_payments)
    AdvancesRepo().extend(advances)


def main():
    # Set the decimal precision explicitly so that we can
    # be sure that it is the same regardless of where
    # it is run, to avoid any possible accounting errors
    getcontext().prec = 10

    process_payments_and_record_updates()


if __name__ == "__main__":
    main()
