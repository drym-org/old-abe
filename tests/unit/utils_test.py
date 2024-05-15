from decimal import Decimal
from oldabe.money_in import (
    calculate_incoming_investment,
    total_amount_paid_to_project,
    calculate_incoming_attribution,
    generate_transactions,
    ROUNDING_TOLERANCE,
    renormalize,
    inflate_valuation,
    process_payments,
)
from oldabe.utils import (
    parse_percentage,
    serialize_proportion,
    get_rounding_difference,
    correct_rounding_error,
)
from oldabe.models import Attribution, Payment
import pytest
from unittest.mock import patch
from .utils import call_sequence
from .fixtures import (
    instruments,
    normalized_attributions,
    excess_attributions,
    shortfall_attributions,
    empty_attributions,
    single_contributor_attributions,
    itemized_payments,
    new_itemized_payments,
)  # noqa


class TestParsePercentage:
    def test_an_integer(self):
        assert parse_percentage('75') == Decimal('0.75')

    def test_non_integer_greater_than_1(self):
        assert parse_percentage('75.334455') == Decimal('0.75334455')

    def test_non_integer_less_than_1(self):
        assert parse_percentage('0.334455') == Decimal('0.00334455')

    def test_decimal_places_at_precision_context(self):
        assert parse_percentage('5.1234567891') == Decimal('0.051234567891')

    def test_very_small_number(self):
        assert parse_percentage('0.000001') == Decimal('0.00000001')

    def test_0(self):
        assert parse_percentage('0') == Decimal('0')

    def test_0_point_0(self):
        assert parse_percentage('0.0') == Decimal('0')

    def test_100(self):
        assert parse_percentage('100') == Decimal('1')

    def test_100_point_0(self):
        assert parse_percentage('100.0') == Decimal('1')


class TestSerializeProportion:
    def test_0(self):
        assert serialize_proportion(Decimal('0')) == '0'

    def test_0_point_0(self):
        assert serialize_proportion(Decimal('0.0')) == '0'

    def test_1(self):
        assert serialize_proportion(Decimal('1')) == '100'

    def test_1_point_0(self):
        assert serialize_proportion(Decimal('1.0')) == '100'

    def test_almost_1(self):
        assert serialize_proportion(Decimal('0.9523452')) == '95.23452'

    def test_low_precision_number(self):
        assert serialize_proportion(Decimal('0.2')) == '20'

    def test_very_small_number(self):
        assert serialize_proportion(Decimal('0.0000002')) == '0.00002'

    def test_decimal_places_at_precision_context(self):
        assert serialize_proportion(Decimal('0.1234567891')) == '12.34567891'


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
