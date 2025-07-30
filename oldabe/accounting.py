from fractions import Fraction


def assert_attributions_normalized(attributions):
    """A complete set of attributions must be normalized, i.e. must add up to
    1. This raises an error if the provided attributions are not normalized."""
    total = _get_attributions_total(attributions)
    print(total)
    assert total == Fraction(1, 1)


def _get_attributions_total(attributions):
    return sum(attributions.values())
