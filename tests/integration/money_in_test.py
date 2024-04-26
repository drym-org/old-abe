import pytest
from datetime import datetime
from decimal import localcontext
import time_machine
from unittest.mock import patch
from oldabe.money_in import (
    process_payments_and_record_updates,
)
from .fixtures import abe_fs
import os


class TestNoPayments:
    @patch('oldabe.money_in.get_git_revision_short_hash', return_value='abcd123')
    def test_no_transactions_generated(self, mock_git_rev, abe_fs):
        with open('abe/price.txt') as f:
            assert f.read() == "10"
        process_payments_and_record_updates()
        with open('./abe/transactions.txt') as f:
            assert f.read() == ""


class TestPaymentAbovePrice:
    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.money_in.get_git_revision_short_hash', return_value='abcd123')
    def test_generates_transactions(self, mock_git_rev, abe_fs):
        amount = 100
        abe_fs.create_file("./abe/payments/1.txt",
                           contents=f"sam,036eaf6,{amount},dummydate")
        process_payments_and_record_updates()
        with open('./abe/transactions.txt') as f:
            # TODO: figure out why it's writing 3 decimal places
            # and decide on handling
            assert f.read() == (
                "old abe,1.000,1.txt,abcd123,1985-10-26 01:24:00\n"
                "DIA,5.000,1.txt,abcd123,1985-10-26 01:24:00\n"
                "sid,47.000000,1.txt,abcd123,1985-10-26 01:24:00\n"
                "jair,28.200000,1.txt,abcd123,1985-10-26 01:24:00\n"
                "ariana,18.800000,1.txt,abcd123,1985-10-26 01:24:00\n"
            )

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.money_in.get_git_revision_short_hash', return_value='abcd123')
    def test_dilutes_attributions(self, mock_git_rev, abe_fs):
        with localcontext() as context:
            context.prec = 2
            amount = 10000
            abe_fs.create_file("./abe/payments/1.txt",
                               contents=f"sam,036eaf6,{amount},dummydate")
            process_payments_and_record_updates()
            with open('./abe/attributions.txt') as f:
                # TODO: figure out why it's writing 3 decimal places
                # and decide on handling
                assert f.read() == (
                    "sid,46\n"
                    "jair,28\n"
                    "ariana,18\n"
                    "sam,8.5\n"
                )


class TestPaymentBelowPrice:
    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.money_in.get_git_revision_short_hash', return_value='abcd123')
    def test_generates_transactions(self, mock_git_rev, abe_fs, fs):
        with localcontext() as context:
            context.prec = 2
            amount = 1
            abe_fs.create_file("./abe/payments/1.txt",
                               contents=f"sam,036eaf6,{amount},dummydate")
            process_payments_and_record_updates()
            with open('./abe/transactions.txt') as f:
                # TODO: figure out why it's writing 3 decimal places
                # and decide on handling
                assert f.read() == (
                    "old abe,0.010,1.txt,abcd123,1985-10-26 01:24:00\n"
                    "DIA,0.050,1.txt,abcd123,1985-10-26 01:24:00\n"
                    "sid,0.47,1.txt,abcd123,1985-10-26 01:24:00\n"
                    "jair,0.28,1.txt,abcd123,1985-10-26 01:24:00\n"
                    "ariana,0.19,1.txt,abcd123,1985-10-26 01:24:00\n"
                )


class UnpayableContributor:
    def test_records_debt(self):
        pass
    def test_debt_paid_on_becoming_payable(self):
        pass
