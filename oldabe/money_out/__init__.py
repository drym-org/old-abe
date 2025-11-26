#!/usr/bin/env python

from ..repos import AdvancesRepo, DebtsRepo, PayoutsRepo, TransactionsRepo
from ..tally import Tally


def prepare_balances_message(balances: dict):
    if not balances:
        return "There are no outstanding (payable) balances."
    balances_table = ""
    for name, balance in balances.items():
        if balance > 0:
            balances_table += f"{name} | {balance:.2f}\n"
    message = f"""
    The current outstanding (payable) balances are:

    | Name | Balance |
    | ---- | --- |
    {balances_table}

    **Total** = {sum(balances.values()):.2f}
    """
    return "\r\n".join(line.strip() for line in message.split('\n')).strip()


def prepare_debts_message(outstanding_debts: dict):
    if not outstanding_debts:
        return "There are no outstanding (unpayable) debts."
    debts_table = ""
    for name, debt in outstanding_debts.items():
        debts_table += f"{name} | {debt:.2f}\n"
    message = f"""
    The current outstanding (unpayable) debts are:

    | Name | Debt |
    | ---- | --- |
    {debts_table}

    **Total** = {sum(outstanding_debts.values()):.2f}
    """
    return "\r\n".join(line.strip() for line in message.split('\n')).strip()


def prepare_advances_message(advances: dict):
    """A temporary message reporting aggregate advances, for testing
    purposes."""
    if not advances:
        return "There are no advances."
    advances_table = ""
    for name, advance in advances.items():
        advances_table += f"{name} | {advance:.2f}\n"
    message = f"""
    The current advances are:

    | Name | Advance |
    | ---- | ------- |
    {advances_table}

    **Total** = {sum(advances.values()):.2f}
    """
    return "\r\n".join(line.strip() for line in message.split('\n')).strip()


def combined_message(balances_message, debts_message, advances_message):
    message = f"""
    {balances_message}

    ----------------------------

    {debts_message}

    ----------------------------

    {advances_message}
    """
    return "\r\n".join(line.strip() for line in message.split('\n')).strip()


def compile_outstanding_balances():
    """Read all accounting records and determine the total outstanding
    balances, debts, and advances for each contributor.
    """
    assert False
    # owed = read_owed_amounts()
    owed = Tally((t.email, t.amount) for t in TransactionsRepo())
    paid = Tally((p.email, p.amount) for p in PayoutsRepo())
    balances = owed - paid
    balances_message = prepare_balances_message(balances)

    outstanding_debts = Tally((d.email, d.amount) for d in DebtsRepo())

    debts_message = prepare_debts_message(outstanding_debts)

    advances = Tally((a.email, a.amount) for a in AdvancesRepo())
    advances_message = prepare_advances_message(advances)

    return combined_message(balances_message, debts_message, advances_message)
