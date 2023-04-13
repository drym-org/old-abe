from decimal import Decimal
from oldabe.money_in import (
    correct_rounding_error,
    get_rounding_difference,
    ROUNDING_TOLERANCE,
    renormalize,
    update_valuation,
)
import pytest
from unittest.mock import patch
from .fixtures import (
    normalized_attributions,
    excess_attributions,
    shortfall_attributions,
)  # noqa


class TestGetRoundingDifference:
    def test_attributions_already_one(self):
        attributions = {'a@b.com': Decimal("0.2"), 'b@c.com': Decimal("0.8")}
        difference = get_rounding_difference(attributions)
        assert difference == Decimal(0)

    def test_attributions_exceed_below_tolerance(self):
        test_diff = ROUNDING_TOLERANCE / Decimal("2")
        attributions = {
            'a@b.com': Decimal("0.2"),
            'b@c.com': Decimal("0.8"),
            'c@d.com': test_diff,
        }
        difference = get_rounding_difference(attributions)
        assert difference == test_diff

    def test_attributions_exceed_above_tolerance(self):
        test_diff = ROUNDING_TOLERANCE * Decimal("2")
        attributions = {
            'a@b.com': Decimal("0.2"),
            'b@c.com': Decimal("0.8"),
            'c@d.com': test_diff,
        }
        with pytest.raises(AssertionError):
            _ = get_rounding_difference(attributions)

    def test_attributions_exceed_by_tolerance(self):
        test_diff = ROUNDING_TOLERANCE
        attributions = {
            'a@b.com': Decimal("0.2"),
            'b@c.com': Decimal("0.8"),
            'c@d.com': test_diff,
        }
        difference = get_rounding_difference(attributions)
        assert difference == test_diff

    def test_attributions_below_one(self):
        test_diff = ROUNDING_TOLERANCE / Decimal("2")
        attributions = {
            'a@b.com': Decimal("0.2"),
            'b@c.com': Decimal("0.8") - test_diff,
        }
        difference = get_rounding_difference(attributions)
        assert difference == -test_diff


# ariana
class TestRenormalize:
    def test_new_investor_5_percent(self, normalized_attributions):
        attributions = normalized_attributions
        renormalized_attributions = {
            'a@b.com': Decimal('0.19'),
            'b@c.com': Decimal('0.76'),
            'c@d.com': Decimal('0.05'),
        }

        incoming_attribution = ['c@d.com', Decimal('0.05')]
        renormalize(attributions, incoming_attribution)
        assert attributions == renormalized_attributions

    def test_new_investor_50_percent(self, normalized_attributions):
        attributions = normalized_attributions
        renormalized_attributions = {
            'a@b.com': Decimal('0.1'),
            'b@c.com': Decimal('0.4'),
            'c@d.com': Decimal('0.5'),
        }

        incoming_attribution = ['c@d.com', Decimal('0.5')]
        renormalize(attributions, incoming_attribution)
        assert attributions == renormalized_attributions

    def test_new_investor_70_percent(self, normalized_attributions):
        attributions = normalized_attributions
        renormalized_attributions = {
            'a@b.com': Decimal('0.06'),
            'b@c.com': Decimal('0.24'),
            'c@d.com': Decimal('0.7'),
        }

        incoming_attribution = ['c@d.com', Decimal('0.7')]
        renormalize(attributions, incoming_attribution)
        assert attributions == renormalized_attributions

    def test_existing_investor_5_percent(self, normalized_attributions):
        attributions = normalized_attributions
        renormalized_attributions = {
            'a@b.com': Decimal('0.19'),
            'b@c.com': Decimal('0.81'),
        }

        incoming_attribution = ['b@c.com', Decimal('0.05')]
        renormalize(attributions, incoming_attribution)
        assert attributions == renormalized_attributions

    def test_existing_investor_50_percent(self, normalized_attributions):
        attributions = normalized_attributions
        renormalized_attributions = {
            'a@b.com': Decimal('0.1'),
            'b@c.com': Decimal('0.9'),
        }

        incoming_attribution = ['b@c.com', Decimal('0.5')]
        renormalize(attributions, incoming_attribution)
        assert attributions == renormalized_attributions

    def test_existing_investor_70_percent(self, normalized_attributions):
        attributions = normalized_attributions
        renormalized_attributions = {
            'a@b.com': Decimal('0.06'),
            'b@c.com': Decimal('0.94'),
        }

        incoming_attribution = ['b@c.com', Decimal('0.7')]
        renormalize(attributions, incoming_attribution)
        assert attributions == renormalized_attributions


class TestCorrectRoundingError:
    @pytest.mark.parametrize(
        "attributions, test_diff",
        [
            ("normalized_attributions", Decimal("0")),
            ("excess_attributions", Decimal("0")),
            ("shortfall_attributions", Decimal("0")),
            ("normalized_attributions", Decimal("0.1")),
            ("excess_attributions", Decimal("0.1")),
            ("shortfall_attributions", Decimal("0.1")),
            ("normalized_attributions", Decimal("-0.1")),
            ("excess_attributions", Decimal("-0.1")),
            ("shortfall_attributions", Decimal("-0.1")),
        ],
    )
    @patch('oldabe.money_in.get_rounding_difference')
    def test_incoming_is_adjusted_by_rounding_error(
        self, mock_rounding_difference, attributions, test_diff, request
    ):
        # Re: request, see: https://stackoverflow.com/q/42014484
        attributions = request.getfixturevalue(attributions)
        mock_rounding_difference.return_value = test_diff
        incoming_email = 'a@b.com'
        incoming_share = attributions[incoming_email]
        other_attributions = attributions.copy()
        other_attributions.pop(incoming_email)
        correct_rounding_error(attributions, incoming_email)
        assert attributions[incoming_email] == incoming_share - test_diff

    @pytest.mark.parametrize(
        "attributions, test_diff",
        [
            ("normalized_attributions", Decimal("0")),
            ("excess_attributions", Decimal("0")),
            ("shortfall_attributions", Decimal("0")),
            ("normalized_attributions", Decimal("0.1")),
            ("excess_attributions", Decimal("0.1")),
            ("shortfall_attributions", Decimal("0.1")),
            ("normalized_attributions", Decimal("-0.1")),
            ("excess_attributions", Decimal("-0.1")),
            ("shortfall_attributions", Decimal("-0.1")),
        ],
    )
    @patch('oldabe.money_in.get_rounding_difference')
    def test_existing_attributions_are_unchanged(
        self, mock_rounding_difference, attributions, test_diff, request
    ):
        attributions = request.getfixturevalue(attributions)
        mock_rounding_difference.return_value = test_diff
        incoming_email = 'a@b.com'
        other_attributions = attributions.copy()
        other_attributions.pop(incoming_email)
        correct_rounding_error(attributions, incoming_email)
        attributions.pop(incoming_email)
        assert attributions == other_attributions


class TestUpdateValuation:
    @patch('oldabe.money_in.open')
    def test_base(self, mock_open):
        amount = 100
        valuation = 1000
        new_valuation = update_valuation(valuation, amount)
        assert new_valuation == amount + valuation


# jair
class TestWriteAttributions:
    pass
