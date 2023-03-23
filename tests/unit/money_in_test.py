from decimal import Decimal
from oldabe.money_in import (
    correct_rounding_error,
    get_rounding_difference,
    ROUNDING_TOLERANCE,
)
import pytest
from unittest.mock import patch


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
    pass


class TestCorrectRoundingError:
    @patch('oldabe.money_in.get_rounding_difference')
    def test_no_rounding_error_incoming_is_unchanged(
        self, mock_rounding_difference
    ):
        mock_rounding_difference.return_value = Decimal("0")
        incoming_email = 'a@b.com'
        incoming_attribution = {incoming_email: Decimal("0.2")}
        prior_attributions = {'b@c.com': Decimal("0.8")}
        attributions = prior_attributions.copy()
        attributions.update(incoming_attribution)
        correct_rounding_error(attributions, incoming_email)
        assert (
            attributions[incoming_email]
            == incoming_attribution[incoming_email]
        )

    @patch('oldabe.money_in.get_rounding_difference')
    def test_no_rounding_error_existing_are_unchanged(
        self, mock_rounding_difference
    ):
        mock_rounding_difference.return_value = Decimal("0")
        incoming_email = 'a@b.com'
        incoming_attribution = {incoming_email: Decimal("0.2")}
        prior_attributions = {'b@c.com': Decimal("0.8")}
        attributions = prior_attributions.copy()
        attributions.update(incoming_attribution)
        correct_rounding_error(attributions, incoming_email)
        attributions.pop(incoming_email)
        assert attributions == prior_attributions

    @patch('oldabe.money_in.get_rounding_difference')
    def test_incoming_attribution_is_adjusted_for_excess(
        self, mock_rounding_difference
    ):
        mock_rounding_difference.return_value = Decimal("0.1")
        incoming_email = 'a@b.com'
        incoming_attribution = {incoming_email: Decimal("0.2")}
        prior_attributions = {'b@c.com': Decimal("0.8")}
        attributions = prior_attributions.copy()
        attributions.update(incoming_attribution)
        correct_rounding_error(attributions, incoming_email)
        assert attributions[incoming_email] == Decimal("0.1")

    @patch('oldabe.money_in.get_rounding_difference')
    def test_existing_attributions_are_unchanged_for_excess(
        self, mock_rounding_difference
    ):
        mock_rounding_difference.return_value = Decimal("0.1")
        incoming_email = 'a@b.com'
        incoming_attribution = {incoming_email: Decimal("0.2")}
        prior_attributions = {'b@c.com': Decimal("0.9")}
        attributions = prior_attributions.copy()
        attributions.update(incoming_attribution)
        correct_rounding_error(attributions, incoming_email)
        attributions.pop(incoming_email)
        assert attributions == prior_attributions

    @patch('oldabe.money_in.get_rounding_difference')
    def test_incoming_attribution_is_adjusted_for_shortfall(
        self, mock_rounding_difference
    ):
        mock_rounding_difference.return_value = Decimal("-0.1")
        incoming_email = 'a@b.com'
        incoming_attribution = {incoming_email: Decimal("0.2")}
        prior_attributions = {'b@c.com': Decimal("0.7")}
        attributions = prior_attributions.copy()
        attributions.update(incoming_attribution)
        correct_rounding_error(attributions, incoming_email)
        assert attributions[incoming_email] == Decimal("0.3")

    @patch('oldabe.money_in.get_rounding_difference')
    def test_existing_attributions_are_unchanged_for_shortfall(
        self, mock_rounding_difference
    ):
        mock_rounding_difference.return_value = Decimal("-0.1")
        incoming_email = 'a@b.com'
        incoming_attribution = {incoming_email: Decimal("0.2")}
        prior_attributions = {'b@c.com': Decimal("0.7")}
        attributions = prior_attributions.copy()
        attributions.update(incoming_attribution)
        correct_rounding_error(attributions, incoming_email)
        attributions.pop(incoming_email)
        assert attributions == prior_attributions


# jair
class TestWriteAttributions:
    pass
