import pytest
from decimal import Decimal
from oldabe.accounting_utils import (
    get_rounding_difference,
    correct_rounding_error,
    ROUNDING_TOLERANCE,
)
from .fixtures import normalized_attributions  # noqa


class TestGetRoundingDifference:
    def test_attributions_already_one(self, normalized_attributions):
        attributions = normalized_attributions
        test_diff = Decimal("0")
        difference = get_rounding_difference(attributions)
        assert difference == test_diff

    def test_attributions_exceed_below_tolerance(
        self, normalized_attributions
    ):
        attributions = normalized_attributions
        test_diff = ROUNDING_TOLERANCE / Decimal("2")
        attributions['c@d.com'] = test_diff
        difference = get_rounding_difference(attributions)
        assert difference == test_diff

    def test_attributions_exceed_above_tolerance(
        self, normalized_attributions
    ):
        attributions = normalized_attributions
        test_diff = ROUNDING_TOLERANCE * Decimal("2")
        attributions['c@d.com'] = test_diff
        with pytest.raises(AssertionError):
            _ = get_rounding_difference(attributions)

    def test_attributions_exceed_by_tolerance(self, normalized_attributions):
        attributions = normalized_attributions
        test_diff = ROUNDING_TOLERANCE
        attributions['c@d.com'] = test_diff
        difference = get_rounding_difference(attributions)
        assert difference == test_diff

    def test_attributions_below_one(self, normalized_attributions):
        attributions = normalized_attributions
        test_diff = ROUNDING_TOLERANCE / Decimal("2")
        attributions['b@c.com'] -= test_diff
        difference = get_rounding_difference(attributions)
        assert difference == -test_diff
