from decimal import Decimal
from oldabe.money_in import (
    calculate_incoming_investment,
    parse_percentage,
    serialize_proportion,
    calculate_incoming_attribution,
    correct_rounding_error,
    generate_transactions,
    get_rounding_difference,
    ROUNDING_TOLERANCE,
    renormalize,
    inflate_valuation,
    process_new_attributable_payments,
)
from oldabe.models import Attribution, Payment
import pytest
from unittest.mock import patch
from .utils import call_sequence
from .fixtures import (
    normalized_attributions,
    excess_attributions,
    shortfall_attributions,
    empty_attributions,
    single_contributor_attributions,
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

    def test_100(self):
        assert parse_percentage('100') == Decimal('1')


class TestSerializeProportion:
    def test_0(self):
        assert serialize_proportion(Decimal('0')) == '0.0'

    # todo - I think we decided we're ok with these trailing zeros?
    def test_almost_1(self):
        assert serialize_proportion(Decimal('0.9523452')) == '95.2345200'

    def test_very_small_number(self):
        assert serialize_proportion(Decimal('0.0000002')) == '0.0000200'

    def test_decimal_places_at_precision_context(self):
        assert serialize_proportion(Decimal('0.1234567891')) == '12.3456789100'


class TestGenerateTransactions:
    def test_zero_amount(self, normalized_attributions):
        with pytest.raises(AssertionError):
            generate_transactions(
                0, normalized_attributions, 'payment-1.txt', 'abc123'
            )

    def test_empty_attributions(self, empty_attributions):
        with pytest.raises(AssertionError):
            generate_transactions(
                100, empty_attributions, 'payment-1.txt', 'abc123'
            )

    def test_single_contributor_attributions(
        self, single_contributor_attributions
    ):
        amount = 100
        payment_file = 'payment-1.txt'
        commit_hash = 'abc123'
        result = generate_transactions(
            amount, single_contributor_attributions, payment_file, commit_hash
        )
        t = result[0]
        assert t.amount == amount

    def test_as_many_transactions_as_attributions(
        self, normalized_attributions
    ):
        amount = 100
        payment_file = 'payment-1.txt'
        commit_hash = 'abc123'
        result = generate_transactions(
            amount, normalized_attributions, payment_file, commit_hash
        )
        assert len(result) == len(normalized_attributions)

    def test_transactions_reflect_attributions(self, normalized_attributions):
        amount = 100
        payment_file = 'payment-1.txt'
        commit_hash = 'abc123'
        result = generate_transactions(
            amount, normalized_attributions, payment_file, commit_hash
        )
        for t in result:
            assert t.amount == normalized_attributions[t.email] * amount

    def test_everyone_in_attributions_are_represented(self, normalized_attributions):
        amount = 100
        payment_file = 'payment-1.txt'
        commit_hash = 'abc123'
        result = generate_transactions(
            amount, normalized_attributions, payment_file, commit_hash
        )
        emails = [t.email for t in result]
        for contributor in normalized_attributions:
            assert contributor in emails

    def test_transaction_refers_to_payment(self, normalized_attributions):
        amount = 100
        payment_file = 'payment-1.txt'
        commit_hash = 'abc123'
        result = generate_transactions(
            amount, normalized_attributions, payment_file, commit_hash
        )
        t = result[0]
        assert t.payment_file == payment_file

    def test_transaction_refers_to_commit(self, normalized_attributions):
        amount = 100
        payment_file = 'payment-1.txt'
        commit_hash = 'abc123'
        result = generate_transactions(
            amount, normalized_attributions, payment_file, commit_hash
        )
        t = result[0]
        assert t.commit_hash == commit_hash


class TestProcessNewAttributablePayments:

    @patch('oldabe.money_in._get_unprocessed_payment_files')
    @patch('oldabe.money_in.read_valuation')
    @patch('oldabe.money_in.read_price')
    @patch('oldabe.money_in.read_payment')
    def test_collects_transactions_for_all_payments(self,
                                                    mock_read_payment,
                                                    mock_read_price,
                                                    mock_read_valuation,
                                                    mock_unprocessed_files,
                                                    normalized_attributions):
        price = 100
        valuation = 1000
        payments = [Payment('a@b.com', 100), Payment('a@b.com', 200)]
        mock_read_payment.side_effect = call_sequence(payments)
        mock_read_price.return_value = price
        mock_read_valuation.return_value = valuation
        mock_unprocessed_files.return_value = payments  # just any list of the right size
        transactions, _ = process_new_attributable_payments(normalized_attributions)
        # generates N transactions for each payment,
        # and there are two payments
        assert len(transactions) == 2 * len(normalized_attributions)


class TestCalculateIncomingAttribution:
    def test_incoming_investment_less_than_zero(self):
        assert calculate_incoming_attribution('a@b.co', -50, 10000) == None

    def test_incoming_investment_is_zero(self):
        assert calculate_incoming_attribution('a@b.co', 0, 10000) == None

    def test_normal_incoming_investment(self):
        assert calculate_incoming_attribution('a@b.co', 50, 10000) == Attribution(
            'a@b.co',
            0.005,
        )

    def test_large_incoming_investment(self):
        assert calculate_incoming_attribution('a@b.co', 5000, 10000) == Attribution(
            'a@b.co',
            0.5,
        )


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

        incoming_attribution = Attribution('c@d.com', Decimal('0.05'))
        renormalize(attributions, incoming_attribution)
        assert attributions == renormalized_attributions

    def test_new_investor_50_percent(self, normalized_attributions):
        attributions = normalized_attributions
        renormalized_attributions = {
            'a@b.com': Decimal('0.1'),
            'b@c.com': Decimal('0.4'),
            'c@d.com': Decimal('0.5'),
        }

        incoming_attribution = Attribution('c@d.com', Decimal('0.5'))
        renormalize(attributions, incoming_attribution)
        assert attributions == renormalized_attributions

    def test_new_investor_70_percent(self, normalized_attributions):
        attributions = normalized_attributions
        renormalized_attributions = {
            'a@b.com': Decimal('0.06'),
            'b@c.com': Decimal('0.24'),
            'c@d.com': Decimal('0.7'),
        }

        incoming_attribution = Attribution('c@d.com', Decimal('0.7'))
        renormalize(attributions, incoming_attribution)
        assert attributions == renormalized_attributions

    def test_existing_investor_5_percent(self, normalized_attributions):
        attributions = normalized_attributions
        renormalized_attributions = {
            'a@b.com': Decimal('0.19'),
            'b@c.com': Decimal('0.81'),
        }

        incoming_attribution = Attribution('b@c.com', Decimal('0.05'))
        renormalize(attributions, incoming_attribution)
        assert attributions == renormalized_attributions

    def test_existing_investor_50_percent(self, normalized_attributions):
        attributions = normalized_attributions
        renormalized_attributions = {
            'a@b.com': Decimal('0.1'),
            'b@c.com': Decimal('0.9'),
        }

        incoming_attribution = Attribution('b@c.com', Decimal('0.5'))
        renormalize(attributions, incoming_attribution)
        assert attributions == renormalized_attributions

    def test_existing_investor_70_percent(self, normalized_attributions):
        attributions = normalized_attributions
        renormalized_attributions = {
            'a@b.com': Decimal('0.06'),
            'b@c.com': Decimal('0.94'),
        }

        incoming_attribution = Attribution('b@c.com', Decimal('0.7'))
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
        incoming_attribution = Attribution(incoming_email, attributions[incoming_email])
        other_attributions = attributions.copy()
        other_attributions.pop(incoming_attribution.email)
        correct_rounding_error(attributions, incoming_attribution)
        assert attributions[incoming_attribution.email] == incoming_attribution.share - test_diff

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
        incoming_attribution = Attribution(incoming_email, attributions[incoming_email])
        other_attributions = attributions.copy()
        other_attributions.pop(incoming_attribution.email)
        correct_rounding_error(attributions, incoming_attribution)
        attributions.pop(incoming_attribution.email)
        assert attributions == other_attributions


class TestInflateValuation:
    @patch('oldabe.money_in.open')
    def test_valuation_inflates_by_fresh_value(self, mock_open):
        amount = 100
        valuation = 1000
        new_valuation = inflate_valuation(valuation, amount)
        assert new_valuation == amount + valuation


class TestCalculateIncomingInvestment:
    @pytest.mark.parametrize(
        "prior_contribution, incoming_amount, price, expected_investment",
        [
            (Decimal("0"), Decimal("0"), Decimal("100"), Decimal("0")),
            (Decimal("0"), Decimal("20"), Decimal("100"), Decimal("0")),
            (Decimal("0"), Decimal("100"), Decimal("100"), Decimal("0")),
            (Decimal("0"), Decimal("120"), Decimal("100"), Decimal("20")),
            (Decimal("20"), Decimal("0"), Decimal("100"), Decimal("0")),
            (Decimal("20"), Decimal("20"), Decimal("100"), Decimal("0")),
            (Decimal("20"), Decimal("80"), Decimal("100"), Decimal("0")),
            (Decimal("20"), Decimal("100"), Decimal("100"), Decimal("20")),
            (Decimal("100"), Decimal("0"), Decimal("100"), Decimal("0")),
            (Decimal("100"), Decimal("20"), Decimal("100"), Decimal("20")),
            (Decimal("120"), Decimal("0"), Decimal("100"), Decimal("0")),
            (Decimal("120"), Decimal("20"), Decimal("100"), Decimal("20")),
        ],
    )
    @patch('oldabe.money_in.total_amount_paid')
    def test_matrix(
        self,
        mock_amount_paid,
        prior_contribution,
        incoming_amount,
        price,
        expected_investment,
    ):
        email = 'dummy@abe.org'
        payment = Payment(email, incoming_amount)
        # this is the total amount paid _including_ the incoming amount
        mock_amount_paid.return_value = prior_contribution + incoming_amount
        result = calculate_incoming_investment(payment, price)
        assert result == expected_investment


# jair
class TestWriteAttributions:
    pass
