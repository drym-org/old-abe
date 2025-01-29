import pytest
from unittest.mock import patch
import time_machine

from datetime import datetime
from decimal import Decimal
from oldabe.distribution import Distribution
from oldabe.models import Advance
from oldabe.money_in.advances import draw_down_advances, advance_payments

from .fixtures import (
    normalized_attributions,
    fresh_debts,
    negative_advances,
)  # noqa


class TestDrawDownAdvances:
    def test_no_advances_exist(self, normalized_attributions):
        distribution = Distribution(normalized_attributions)
        negative_advances = draw_down_advances(
            100, distribution, [], 'payment-10.txt'
        )
        assert negative_advances == []

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    @patch(
        'oldabe.money_in.advances.Tally',
        return_value={'a@b.com': Decimal(100)},
    )
    def test_existing_advance_greater_than_payment_amount(
        self, mock_tally, mock_git_rev, normalized_attributions
    ):
        expected_advance = Advance(
            email='a@b.com',
            amount=Decimal('-20.0'),
            payment_file='payment-10.txt',
        )
        distribution = Distribution(normalized_attributions)
        negative_advances = draw_down_advances(
            100, distribution, [], 'payment-10.txt'
        )
        assert negative_advances == [expected_advance]

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    @patch(
        'oldabe.money_in.advances.Tally', return_value={'a@b.com': Decimal(10)}
    )
    def test_existing_advance_less_than_payment_amount(
        self, mock_tally, mock_git_rev, normalized_attributions
    ):
        expected_advance = Advance(
            email='a@b.com',
            amount=Decimal('-10.0'),
            payment_file='payment-10.txt',
        )
        distribution = Distribution(normalized_attributions)
        negative_advances = draw_down_advances(
            100, distribution, [], 'payment-10.txt'
        )
        assert negative_advances == [expected_advance]

    @patch(
        'oldabe.money_in.advances.Tally', return_value={'a@b.com': Decimal(10)}
    )
    def test_contributor_is_unpayable(
        self, mock_tally, normalized_attributions
    ):
        distribution = Distribution(normalized_attributions)
        negative_advances = draw_down_advances(
            100, distribution, ['a@b.com'], 'payment-10.txt'
        )
        assert negative_advances == []


class TestAdvancePayments:
    def test_empty_redistribution_pot(self, normalized_attributions):
        distribution = Distribution(normalized_attributions)
        fresh_advances = advance_payments(
            [], [], distribution, [], 'payment-10.txt'
        )
        assert fresh_advances == []

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    def test_fresh_debts_and_neg_advances_present(
        self, normalized_attributions, fresh_debts, negative_advances
    ):
        expected_advance_a = Advance(
            email='a@b.com',
            amount=Decimal('20.0'),
            payment_file='payment-10.txt',
        )
        expected_advance_b = Advance(
            email='b@c.com',
            amount=Decimal('80.0'),
            payment_file='payment-10.txt',
        )
        distribution = Distribution(normalized_attributions)
        fresh_advances = advance_payments(
            fresh_debts, negative_advances, distribution, [], 'payment-10.txt'
        )
        assert fresh_advances == [expected_advance_a, expected_advance_b]

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    def test_unpayable_contributor_present(
        self, normalized_attributions, fresh_debts, negative_advances
    ):
        expected_advance_b = Advance(
            email='b@c.com',
            amount=Decimal('100.0'),
            payment_file='payment-10.txt',
        )
        distribution = Distribution(normalized_attributions)
        fresh_advances = advance_payments(
            fresh_debts,
            negative_advances,
            distribution,
            ['a@b.com'],
            'payment-10.txt',
        )
        assert fresh_advances == [expected_advance_b]
