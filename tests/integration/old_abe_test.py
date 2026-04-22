import os
from datetime import datetime
from unittest.mock import patch

import pytest
import time_machine
from fractions import Fraction

from oldabe.money_in import process_payments_and_record_updates
from oldabe.money_in.equity import decimal_to_fraction
from oldabe.money_out import compile_outstanding_balances
from oldabe.distribution import Distribution
from oldabe.repos import AdvancesRepo, TransactionsRepo, DebtsRepo
from oldabe.tally import Tally

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
    def test_advances_equal_debts(self, mock_git_rev, abe_fs):
        amount = 100
        with open("./abe/price.txt", "w") as f:
            f.write("100000")
        abe_fs.create_file(
            "./abe/payments/1.txt",
            contents=f"sam,036eaf6,{amount},1987-06-30 06:25:00",
        )
        abe_fs.create_file(
            "./abe/unpayable_contributors.txt",
            contents=f"jair\nDIA",
        )
        process_payments_and_record_updates()

        advances = AdvancesRepo()
        total_advances = sum(a.amount for a in advances)
        debts = DebtsRepo()
        total_debts = sum(d.amount for d in debts)
        assert total_advances == total_debts

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

    # TODO: in some cases (either the advances exceed the payment amount or
    # there are no payable contributors), there would likely be no transactions
    # created. This would lead the payment to be considered unprocessed, which
    # would cause it to be processed again the next time, since we determine
    # this by checking whether it appears in the transactions file.
    # 1. Add a test for this validating the bug
    # 2. Fix it

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    def test_compiled_outstanding_balances(self, mock_git_rev, abe_fs):
        self._call(abe_fs)
        message = compile_outstanding_balances()
        assert (
            "| Name | Debt |\r\n" "| ---- | --- |\r\n" "ariana | 0.00\r\n"
        ) in message


def _print_accounting_files(index):
    with open("./abe/debts.txt") as f:
        print(f"[{index}] Debts are:\n{f.read()}")
    with open("./abe/advances.txt") as f:
        print(f"[{index}] Advances are:\n{f.read()}")


# TODO: add a separate test for unpayable instrument (in addition?)
#       -> note: newer instrument debts are paid before older project debts
#       -> that may be considered unfair.
#       -> decide on how to handle this
# TODO: test all contributors are unpayable (e.g., likely to happen
#       often with instruments)
# TODO: should we make instruments total to 100 instead of using None? Yes. How?
#   Options:
#    1. Add a None sentinel value as a standard syntax of attribution files
#      (used only in instruments, not in contributors)
#    2. Add a new configuration-level file similar to price.txt and valuation.txt
#       that indicates the percentage breakdown across attributions files
#    3. What today is deciding when to put None in a distribution and renormalize?
#       Could use that everywhere.
#    -> Note: superseded by the plan below:

# Provisional plan for uniform handling of debts and advances instead of
# separate processing of instruments/contributors:
#
# 1. Keep instruments.txt and contributors.txt as separate files
# 2. Compose a single "attributions" dictionary from these two for process_payment,
#    i.e., we only do this once rather than in two stages
# 3. In other cases, for handle_investment (dilution of shares/ inflation of valuation),
#    we just use contributors in creating the attributions dictionary
#
# If there are no payable contributors in either instruments or contributors,
#  Short term: Reject payment (in practice: don't even record; just put it in pending/ publicly)
#  Long term: Could consider the project itself (i.e., the trustee) as receiving the money
#            + record debts to all contributors and instruments
#            + record an advance to the project?
#            -> But never create an actual transaction for the project
#               (they are never entitled to any money)
#  Long term option B:
#   Have a zero share instrument for the trustee (who is always payable)
#   And just "divide fairly among" all payable contributors would probably work
#   even though the share is zero?

class TestAdvancesModeling:

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    def test_fair_payouts_after_advances_reach_steady_state(self, mock_git_rev, abe_fs):
        # one payment, one unpayable contributor
        # make the contributor payable
        # process some payments and see what happens to the advances

        amount = 100
        # set a high price to ensure no new payer becomes attributed
        with open("./abe/price.txt", "w") as f:
            f.write("100000")
        abe_fs.create_file(
            "./abe/payments/1.txt",
            contents=f"sam,036eaf6,{amount},1987-06-30 06:25:00",
        )
        abe_fs.create_file(
            "./abe/unpayable_contributors.txt",
            contents=f"jair\nDIA",
        )
        process_payments_and_record_updates()

        os.remove("./abe/unpayable_contributors.txt")

        for i, payer in enumerate(["sam", "samy", "doris", "jair"]):
            # expect debts to be paid off
            # and advances to reach some steady state (what? TBD)
            abe_fs.create_file(
                f"./abe/payments/{i+2}.txt",
                contents=f"{payer},036eaf6,{amount},1987-06-30 06:25:00",
            )
            process_payments_and_record_updates()

        # assert 3 things:
        # 1. distribution of advance balances should equal attribution proportions
        # (note that the advances do remain indefinitely, but in a way that
        # achieve the correct distributions upon reaching this steady state)
        contributor_emails = ["sid", "jair", "ariana"]
        advances = AdvancesRepo()
        d = Distribution(**{k: decimal_to_fraction(v) for k, v in Tally([(a.email, a.amount) for a in advances if a.email in contributor_emails]).items()}).distribute(100)
        assert 49.9 <= d["sid"] <= 50.1
        assert 29.9 <= d["jair"] <= 30.1
        assert 19.9 <= d["ariana"] <= 20.1

        d = Distribution(**{k: decimal_to_fraction(v) for k, v in Tally([(a.email, a.amount) for a in advances if a.email not in contributor_emails]).items()}).distribute(6)
        assert 0.9 <= d["old abe"] <= 1.1
        assert 4.9 <= d["DIA"] <= 5.1

        # 2. distribution of payouts, i.e., transactions, should also be proportional to attributions.
        # when you exclude instruments (note that instruments did not have advances created for them
        # since there was no unpayable instrument)
        contributor_emails = ["sid", "jair", "ariana"]
        transactions = TransactionsRepo()
        d = Distribution(**{k: decimal_to_fraction(v) for k, v in Tally([(t.email, t.amount) for t in transactions if t.email in contributor_emails]).items()}).distribute(100)
        assert 49.9 <= d["sid"] <= 50.1
        assert 29.9 <= d["jair"] <= 30.1
        assert 19.9 <= d["ariana"] <= 20.1

        d = Distribution(**{k: decimal_to_fraction(v) for k, v in Tally([(t.email, t.amount) for t in transactions if t.email not in contributor_emails]).items()}).distribute(6)
        assert 0.9 <= d["old abe"] <= 1.1
        assert 4.9 <= d["DIA"] <= 5.1

        # 3. debts should be zero for everyone.
        debts = DebtsRepo()
        debts = Tally([(d.email, d.amount) for d in debts]).values()
        assert sum(debts) == 0

    @time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
    @patch('oldabe.models.default_commit_hash', return_value='abcd123')
    def test_all_contributors_are_unpayable(self, mock_git_rev, abe_fs):

        amount = 100
        # set a high price to ensure no new payer becomes attributed
        with open("./abe/price.txt", "w") as f:
            f.write("100000")
        abe_fs.create_file(
            "./abe/payments/1.txt",
            contents=f"sam,036eaf6,{amount},1987-06-30 06:25:00",
        )
        abe_fs.create_file(
            "./abe/unpayable_contributors.txt",
            contents=f"old abe\nDIA",
        )
        process_payments_and_record_updates()

        _print_accounting_files(1)
