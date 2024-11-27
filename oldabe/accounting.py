from decimal import Decimal

ROUNDING_TOLERANCE = Decimal("0.000001")


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


def correct_rounding_error(attributions, incoming_attribution):
    """Due to finite precision, the Decimal module will round up or down
    on the last decimal place. This could result in the aggregate value not
    quite totaling to 1. This corrects that total by either adding or
    subtracting the difference from the incoming attribution (by convention).
    """
    difference = get_rounding_difference(attributions)
    attributions[incoming_attribution.email] -= difference


def assert_attributions_normalized(attributions):
    """A complete set of attributions must be normalized, i.e. must add up to
    1. This raises an error if the provided attributions are not normalized."""
    print(_get_attributions_total(attributions))
    assert _get_attributions_total(attributions) == Decimal("1")


def _get_attributions_total(attributions):
    return sum(attributions.values())
