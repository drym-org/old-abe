from oldabe.money_out import (
    compute_balances,
    prepare_balances_message,
)
from collections import defaultdict
import pytest


class TestComputeBalances:
    @pytest.mark.parametrize(
        "owed, paid, expected_balances",
        [
            (
                defaultdict(int),
                defaultdict(int),
                {},
            ),  # owed nothing, paid nothing
            (
                defaultdict(int, {'a': 100}),
                defaultdict(int),
                {'a': 100},
            ),  # owed something, paid nothing
            (
                defaultdict(int),
                defaultdict(int, {'a': 100}),
                {},
            ),  # owed nothing, paid something
            (
                defaultdict(int, {'a': 100}),
                defaultdict(int, {'a': 80}),
                {'a': 20},
            ),  # owed something, paid something
            (
                defaultdict(int, {'a': 100}),
                defaultdict(int, {'a': 100}),
                {},
            ),  # owed something, paid in full
            (
                defaultdict(int, {'a': 100}),
                defaultdict(int, {'a': 120}),
                {},
            ),  # owed something, overpaid
            (
                defaultdict(int, {'a': 100, 'b': 200}),
                defaultdict(int, {'a': 80}),
                {'a': 20, 'b': 200},
            ),  # more than one contributor
            (
                defaultdict(int, {'a': 100, 'b': 200}),
                defaultdict(int, {'a': 80, 'b': 100}),
                {'a': 20, 'b': 100},
            ),  # more than one contributor
        ],
    )
    def test_matrix(self, owed, paid, expected_balances):
        result = compute_balances(owed, paid)
        assert result == expected_balances


class TestPrepareMessage:
    @pytest.mark.parametrize(
        "balances",
        [
            {'abc@abe.com': 20, 'pqr@abe.com': 50},
            {'abc@abe.com': 20},
            {'abc@abe.com': 20, 'pqr@abe.com': 50, 'zab@abe.com': 10},
        ],
    )
    def test_matrix(self, balances):
        result = prepare_balances_message(balances)
        for k in balances.keys():
            assert k in result

    def test_no_balances(self):
        balances = {}
        result = prepare_balances_message(balances)
        assert result == "There are no outstanding (payable) balances."
