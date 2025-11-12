import os
from datetime import datetime
from unittest.mock import patch

import pytest
import time_machine

from oldabe.money_in import process_payments_and_record_updates
from oldabe.money_out import compile_outstanding_balances

from .fixtures import abe_fs


class TestNoPayments:

    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    def test_no_transactions_generated(self, mock_git_rev, abe_fs):
        process_payments_and_record_updates()
        with open('./abe/transactions.txt') as f:
            assert f.read() == ""

    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    def test_compiled_outstanding_balances(self, mock_git_rev, abe_fs):
        process_payments_and_record_updates()
        message = compile_outstanding_balances()
        assert "There are no outstanding (payable) balances." in message
        assert "There are no outstanding (unpayable) debts." in message
        assert "There are no advances." in message


# TODO: in some cases even though the value is e.g. 1,
# it's writing out 3 decimal places, like 1.000. We should
# figure out why this is happening (and whether it's OK)
# and decide on appropriate handling


class TestPaymentAbovePrice:

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    def test_generates_transactions(self, mock_git_rev, abe_fs):
        amount = 100
        abe_fs.create_file(
            "./abe/payments/1.txt",
            contents=f"sam,036eaf6,{amount},1987-06-30 06:25:00",
        )
        process_payments_and_record_updates()
        with open('./abe/transactions.txt') as f:
            assert f.read() == (
                "old abe,1.00,1.txt,abcd123,1985-10-26 01:24:00\n"
                "DIA,5.00,1.txt,abcd123,1985-10-26 01:24:00\n"
                "sid,47.00,1.txt,abcd123,1985-10-26 01:24:00\n"
                "jair,28.20,1.txt,abcd123,1985-10-26 01:24:00\n"
                "ariana,18.80,1.txt,abcd123,1985-10-26 01:24:00\n"
            )

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    def test_dilutes_attributions(self, mock_git_rev, abe_fs):
        amount = 10000
        abe_fs.create_file(
            "./abe/payments/1.txt",
            contents=f"sam,036eaf6,{amount},1987-06-30 06:25:00",
        )
        process_payments_and_record_updates()
        with open('./abe/attributions.txt') as f:
            assert f.read() == (
                "sid,5000/10939\n"
                "jair,3000/10939\n"
                "ariana,2000/10939\n"
                "sam,939/10939\n"
            )
        with open('./abe/attributions.md') as f:
            assert f.read() == (
                "# Contributors\n"
                "\n"
                "| Name | Share |\n"
                "| ---- | ----- |\n"
                "sid | 45.71%\n"
                "jair | 27.42%\n"
                "ariana | 18.28%\n"
                "sam | 8.58%"
            )

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    def test_small_payment_dilutes_attributions(self, mock_git_rev, abe_fs):
        amount = 1000
        abe_fs.create_file(
            "./abe/payments/1.txt",
            contents=f"sam,036eaf6,{amount},1987-06-30 06:25:00",
        )
        process_payments_and_record_updates()
        with open('./abe/attributions.txt') as f:
            assert f.read() == (
                "sid,5000/10093\n"
                "jair,3000/10093\n"
                "ariana,2000/10093\n"
                "sam,93/10093\n"
            )
        with open('./abe/attributions.md') as f:
            assert f.read() == (
                "# Contributors\n"
                "\n"
                "| Name | Share |\n"
                "| ---- | ----- |\n"
                "sid | 49.54%\n"
                "jair | 29.72%\n"
                "ariana | 19.82%\n"
                "sam | 0.92%"
            )

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    def test_compiled_outstanding_balances(self, mock_git_rev, abe_fs):
        amount = 100
        abe_fs.create_file(
            "./abe/payments/1.txt",
            contents=f"sam,036eaf6,{amount},1987-06-30 06:25:00",
        )
        process_payments_and_record_updates()

        message = compile_outstanding_balances()

        assert (
            "| Name | Balance |\r\n" "| ---- | --- |\r\n" "old abe | 1.00\r\n"
        ) in message


class TestPaymentBelowPrice:

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    def test_generates_transactions(self, mock_git_rev, abe_fs):
        amount = 1
        abe_fs.create_file(
            "./abe/payments/1.txt",
            contents=f"sam,036eaf6,{amount},1987-06-30 06:25:00",
        )
        process_payments_and_record_updates()
        with open('./abe/transactions.txt') as f:
            assert f.read() == (
                "old abe,0.01,1.txt,abcd123,1985-10-26 01:24:00\n"
                "DIA,0.05,1.txt,abcd123,1985-10-26 01:24:00\n"
                "sid,0.47,1.txt,abcd123,1985-10-26 01:24:00\n"
                "jair,0.28,1.txt,abcd123,1985-10-26 01:24:00\n"
                "ariana,0.19,1.txt,abcd123,1985-10-26 01:24:00\n"
            )

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    def test_compiled_outstanding_balances(self, mock_git_rev, abe_fs):
        amount = 1
        abe_fs.create_file(
            "./abe/payments/1.txt",
            contents=f"sam,036eaf6,{amount},1987-06-30 06:25:00",
        )
        process_payments_and_record_updates()
        message = compile_outstanding_balances()

        assert (
            "| Name | Balance |\r\n" "| ---- | --- |\r\n" "old abe | 0.01\r\n"
        ) in message


class TestNonAttributablePayment:

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    def test_does_not_dilute_attributions(self, mock_git_rev, abe_fs):
        amount = 100
        abe_fs.create_file(
            "./abe/payments/nonattributable/1.txt",
            contents=f"sam,036eaf6,{amount},1987-06-30 06:25:00",
        )
        process_payments_and_record_updates()
        with open('./abe/attributions.txt') as f:
            assert f.read() == ("sid,1/2\n" "jair,3/10\n" "ariana,1/5\n")
        with open('./abe/attributions.md') as f:
            assert f.read() == (
                "# Contributors\n"
                "\n"
                "| Name | Share |\n"
                "| ---- | ----- |\n"
                "sid | 50.00%\n"
                "jair | 30.00%\n"
                "ariana | 20.00%"
            )

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    def test_generates_transactions(self, mock_git_rev, abe_fs):
        amount = 100
        abe_fs.create_file(
            "./abe/payments/1.txt",
            contents=f"sam,036eaf6,{amount},1987-06-30 06:25:00",
        )
        process_payments_and_record_updates()
        with open('./abe/transactions.txt') as f:
            assert f.read() == (
                "old abe,1.00,1.txt,abcd123,1985-10-26 01:24:00\n"
                "DIA,5.00,1.txt,abcd123,1985-10-26 01:24:00\n"
                "sid,47.00,1.txt,abcd123,1985-10-26 01:24:00\n"
                "jair,28.20,1.txt,abcd123,1985-10-26 01:24:00\n"
                "ariana,18.80,1.txt,abcd123,1985-10-26 01:24:00\n"
            )

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    def test_compiled_outstanding_balances(self, mock_git_rev, abe_fs):
        amount = 100
        abe_fs.create_file(
            "./abe/payments/nonattributable/1.txt",
            contents=f"sam,036eaf6,{amount},1987-06-30 06:25:00",
        )
        process_payments_and_record_updates()
        message = compile_outstanding_balances()

        assert (
            "| Name | Balance |\r\n" "| ---- | --- |\r\n" "old abe | 1.00\r\n"
        ) in message


class TestUnpayableContributor:

    def _call(self, abe_fs):
        amount = 100
        abe_fs.create_file(
            "./abe/payments/1.txt",
            contents=f"sam,036eaf6,{amount},1987-06-30 06:25:00",
        )
        abe_fs.create_file(
            "./abe/unpayable_contributors.txt", contents=f"ariana"
        )
        process_payments_and_record_updates()

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    def test_generates_transactions(self, mock_git_rev, abe_fs):
        self._call(abe_fs)
        with open('./abe/transactions.txt') as f:
            assert f.read() == (
                "old abe,1.00,1.txt,abcd123,1985-10-26 01:24:00\n"
                "DIA,5.00,1.txt,abcd123,1985-10-26 01:24:00\n"
                "sid,58.75,1.txt,abcd123,1985-10-26 01:24:00\n"
                "jair,35.25,1.txt,abcd123,1985-10-26 01:24:00\n"
            )

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    def test_records_debt(self, mock_git_rev, abe_fs):
        self._call(abe_fs)
        with open('./abe/debts.txt') as f:
            assert f.read() == (
                "ariana,18.80,1.txt,abcd123,1985-10-26 01:24:00\n"
            )

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    def test_records_advances(self, mock_git_rev, abe_fs):
        # advances for payable people
        # and none for unpayable
        self._call(abe_fs)
        with open('./abe/advances.txt') as f:
            assert f.read() == (
                "sid,11.75,1.txt,abcd123,1985-10-26 01:24:00\n"
                "jair,7.05,1.txt,abcd123,1985-10-26 01:24:00\n"
            )

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    def test_compiled_outstanding_balances(self, mock_git_rev, abe_fs):
        self._call(abe_fs)
        message = compile_outstanding_balances()
        assert (
            "| Name | Debt |\r\n" "| ---- | --- |\r\n" "ariana | 18.80\r\n"
        ) in message


class TestUnpayableContributorBecomesPayable:

    def _call(self, abe_fs):
        amount = 100
        abe_fs.create_file(
            "./abe/payments/1.txt",
            contents=f"sam,036eaf6,{amount},1987-06-30 06:25:00",
        )
        abe_fs.create_file(
            './abe/transactions.txt',
            contents=(
                "old abe,1.00,1.txt,abcd123,1985-10-26 01:24:00\n"
                "DIA,5.00,1.txt,abcd123,1985-10-26 01:24:00\n"
                "sid,58.75,1.txt,abcd123,1985-10-26 01:24:00\n"
                "jair,35.25,1.txt,abcd123,1985-10-26 01:24:00\n"
            ),
        )
        abe_fs.create_file(
            "./abe/debts.txt",
            contents="ariana,18.80,1.txt,abcd123,1985-10-26 01:24:00\n",
        )

        abe_fs.create_file(
            "./abe/advances.txt",
            contents=(
                "sid,11.75,1.txt,abcd123,1985-10-26 01:24:00\n"
                "jair,7.05,1.txt,abcd123,1985-10-26 01:24:00\n"
            ),
        )
        abe_fs.create_file(
            "./abe/payments/2.txt",
            contents=f"sam,036eaf6,{amount},1987-06-30 06:25:00",
        )
        process_payments_and_record_updates()

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    def test_debt_paid(self, mock_git_rev, abe_fs):
        self._call(abe_fs)
        with open('./abe/debts.txt') as f:
            assert f.read() == (
                "ariana,18.80,1.txt,abcd123,1985-10-26 01:24:00\n"
                "ariana,-18.80,2.txt,abcd123,1985-10-26 01:24:00\n"
            )

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    def test_transactions(self, mock_git_rev, abe_fs):
        # here, because the two payment amounts are the same,
        # it ends up correcting immediately. We might consider
        # more tests where the second amount is larger, or
        # where there are more debts
        self._call(abe_fs)
        with open('./abe/transactions.txt') as f:
            assert f.read() == (
                "old abe,1.00,1.txt,abcd123,1985-10-26 01:24:00\n"
                "DIA,5.00,1.txt,abcd123,1985-10-26 01:24:00\n"
                "sid,58.75,1.txt,abcd123,1985-10-26 01:24:00\n"
                "jair,35.25,1.txt,abcd123,1985-10-26 01:24:00\n"
                "old abe,1.00,2.txt,abcd123,1985-10-26 01:24:00\n"
                "DIA,5.00,2.txt,abcd123,1985-10-26 01:24:00\n"
                "sid,35.25,2.txt,abcd123,1985-10-26 01:24:00\n"
                "jair,21.15,2.txt,abcd123,1985-10-26 01:24:00\n"
                "ariana,37.60,2.txt,abcd123,1985-10-26 01:24:00\n"
            )

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    def test_advances(self, mock_git_rev, abe_fs):
        self._call(abe_fs)
        with open('./abe/advances.txt') as f:
            assert f.read() == (
                "sid,11.75,1.txt,abcd123,1985-10-26 01:24:00\n"
                "jair,7.05,1.txt,abcd123,1985-10-26 01:24:00\n"
                "sid,-11.75,2.txt,abcd123,1985-10-26 01:24:00\n"
                "jair,-7.05,2.txt,abcd123,1985-10-26 01:24:00\n"
                "sid,9.40,2.txt,abcd123,1985-10-26 01:24:00\n"
                "jair,5.64,2.txt,abcd123,1985-10-26 01:24:00\n"
                "ariana,3.76,2.txt,abcd123,1985-10-26 01:24:00\n"
            )

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    def test_compiled_outstanding_balances(self, mock_git_rev, abe_fs):
        self._call(abe_fs)
        message = compile_outstanding_balances()
        assert (
            "| Name | Debt |\r\n" "| ---- | --- |\r\n" "ariana | 0.00\r\n"
        ) in message
