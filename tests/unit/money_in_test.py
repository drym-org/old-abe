from decimal import Decimal
from oldabe.money_in import (
    get_rounding_difference,
    ROUNDING_TOLERANCE,
)
import pytest


class TestGetRoundingDifference:

    def test_attributions_already_one(self):
        attributions = {'a@b.com': Decimal("0.2"), 'b@c.com': Decimal("0.8")}
        difference = get_rounding_difference(attributions)
        assert difference == Decimal(0)

    def test_attributions_exceed_below_tolerance(self):
        small_difference = ROUNDING_TOLERANCE / Decimal("2")
        attributions = {'a@b.com': Decimal("0.2"), 'b@c.com': Decimal("0.8"), 'c@d.com': small_difference}
        difference = get_rounding_difference(attributions)
        assert difference == small_difference

    def test_attributions_exceed_above_tolerance(self):
        big_difference = ROUNDING_TOLERANCE * Decimal("2")
        attributions = {'a@b.com': Decimal("0.2"), 'b@c.com': Decimal("0.8"), 'c@d.com': big_difference}
        with pytest.raises(AssertionError):
            _ = get_rounding_difference(attributions)

    def test_attributions_exceed_by_tolerance(self):
        normal_difference = ROUNDING_TOLERANCE
        attributions = {'a@b.com': Decimal("0.2"), 'b@c.com': Decimal("0.8"), 'c@d.com': normal_difference}
        difference = get_rounding_difference(attributions)
        assert difference == normal_difference

    def test_attributions_below_one(self):
        small_difference = ROUNDING_TOLERANCE / Decimal("2")
        attributions = {'a@b.com': Decimal("0.2"), 'b@c.com': Decimal("0.8") - small_difference}
        difference = get_rounding_difference(attributions)
        assert difference == -small_difference


# ariana
class TestRenormalize:
    pass


# sid
class TestCorrectRoundingError:
    pass


# jair
class TestWriteAttributions:
    pass
