from decimal import Decimal
import pytest
from unittest.mock import patch
from oldabe.models import Payment, ItemizedPayment, Attribution
from oldabe.money_in.equity import calculate_incoming_investment, calculate_incoming_attribution, dilute_attributions, handle_investment
from .fixtures import normalized_attributions  # noqa


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
    @patch('oldabe.money_in.equity.ItemizedPaymentsRepo')
    def test_matrix(
            self,
            prior_itemized_payments,
            prior_contribution,
            incoming_amount,
            price,
            expected_investment,
     ):
        email = 'dummy@abe.org'
        payment = Payment(email, email, incoming_amount)
        # this is the total amount paid _including_ the incoming amount
        prior_itemized_payments.return_value = (
            [ItemizedPayment(email, 0, prior_contribution, True, 'dummy.file')]
        )
        new_itemized_payments = [ItemizedPayment(email, 0, incoming_amount, True, 'dummy.file')]
        result = calculate_incoming_investment(payment, price, new_itemized_payments)
        assert result == expected_investment


class TestCalculateIncomingAttribution:
    @pytest.mark.parametrize(
        "incoming_investment, expected_attribution",
        [
            (Decimal("0"), Decimal('0')),
            (Decimal("50"), Decimal('0.005')),
            (Decimal("5000"), Decimal('0.5')),
        ],
    )
    def test_matrix(
            self,
            incoming_investment,
            expected_attribution,
    ):
        email = 'a@b.co'
        posterior_valuation = Decimal('10000')

        attribution = calculate_incoming_attribution(
            email, incoming_investment, posterior_valuation
        )
        assert (
            attribution.share == expected_attribution
        )


class TestDiluteAttributions:

    @pytest.mark.parametrize(
        "incoming_attribution, expected_attribution",
        [
            (Decimal("0"), Decimal('0.2')),
            (Decimal("0.1"), Decimal('0.28')),
            (Decimal("0.5"), Decimal('0.60')),
        ],
    )
    def test_matrix(
            self,
            incoming_attribution,
            expected_attribution,
            normalized_attributions,
    ):
        email = 'a@b.com'
        incoming_attribution = Attribution(email, incoming_attribution)

        dilute_attributions(
            incoming_attribution, normalized_attributions
        )
        a_share = normalized_attributions[email]
        b_share = normalized_attributions['b@c.com']
        assert (
            a_share == expected_attribution
        )
        assert (
            b_share == 1 - expected_attribution
        )


class TestHandleInvestment:

    def test_dilutes_attributions(
        self,
        normalized_attributions,
    ):
        apriori_share = normalized_attributions['a@b.com']
        email = 'dummy@abe.org'
        payment = Payment(email, email, Decimal('90'))
        itemized = ItemizedPayment(
                email,
                10,
                90,
                payment.attributable,
                payment.file,
            )
        new_itemized_payments = [itemized]
        price = Decimal('10')
        prior_valuation = Decimal('50')

        _valuation = handle_investment(payment,
                                       new_itemized_payments,
                                       normalized_attributions,
                                       price,
                                       prior_valuation)
        assert normalized_attributions['a@b.com'] < apriori_share
        assert sum(normalized_attributions.values()) == Decimal('1')

    def test_inflates_valuation(
        self,
        normalized_attributions,
    ):
        email = 'dummy@abe.org'
        payment = Payment(email, email, Decimal('90'))
        itemized = ItemizedPayment(
                email,
                10,
                90,
                payment.attributable,
                payment.file,
            )
        new_itemized_payments = [itemized]
        price = Decimal('10')
        prior_valuation = Decimal('50')

        valuation = handle_investment(payment,
                                      new_itemized_payments,
                                      normalized_attributions,
                                      price,
                                      prior_valuation)
        assert valuation == (prior_valuation + 80)
