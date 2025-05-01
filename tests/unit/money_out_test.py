from oldabe.money_out import (
    prepare_balances_message,
    prepare_debts_message,
)
import pytest


class TestPrepareBalancesMessage:
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


class TestPrepareDebtsMessage:
    @pytest.mark.parametrize(
        'debts',
        [
            {'abc@abe.com': 20, 'pqr@abe.com': 50},
            {'abc@abe.com': 20},
            {'abc@abe.com': 20, 'pqr@abe.com': 50, 'zab@abe.com': 10},
        ],
    )
    def test_matrix(self, debts):
        result = prepare_debts_message(debts)
        for k in debts.keys():
            assert k in result

    def test_no_debts(self):
        debts = {}
        result = prepare_debts_message(debts)
        assert result == "There are no outstanding (unpayable) debts."
