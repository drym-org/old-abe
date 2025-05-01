from decimal import Decimal
from ..constants import (
    ATTRIBUTIONS_FILE,
    ACCOUNTING_ZERO,
)
from ..parsing import serialize_proportion
from ..accounting import (
    assert_attributions_normalized,
    correct_rounding_error,
)
from ..repos import ItemizedPaymentsRepo
from ..models import Attribution
import csv


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


def calculate_incoming_investment(
    payment, price, new_itemized_payments, prior_itemized_payments
):
    """
    If the payment brings the aggregate amount paid by the payee
    above the price, then that excess is treated as investment.
    """
    total_attributable_payments = sum(
        p.project_amount
        for p in [*prior_itemized_payments, *new_itemized_payments]
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
        return Attribution(email, Decimal('0'))


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
    prior_itemized_payments = ItemizedPaymentsRepo()
    incoming_investment = calculate_incoming_investment(
        payment, price, new_itemized_payments, prior_itemized_payments
    )
    # inflate valuation by the amount of the fresh investment
    posterior_valuation = prior_valuation + incoming_investment

    incoming_attribution = calculate_incoming_attribution(
        payment.email, incoming_investment, posterior_valuation
    )
    if incoming_attribution and incoming_attribution.share > ACCOUNTING_ZERO:
        dilute_attributions(incoming_attribution, attributions)
    return posterior_valuation
