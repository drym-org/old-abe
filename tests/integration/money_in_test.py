import pytest
from datetime import datetime
import time_machine
from unittest.mock import patch
from oldabe.money_in import (
    process_payments_and_record_updates,
)
import os


@patch('oldabe.money_in.get_git_revision_short_hash', return_value='abcd123')
def test_no_transactions_if_no_payments(mock_git_rev, fs):
    fs.create_file("./abe/price.txt", contents="10")
    fs.create_file("./abe/valuation.txt", contents="100000")
    fs.create_file("./abe/instruments.txt", contents="""
        old abe,1
        DIA,5
        """)
    fs.create_file("./abe/attributions.txt", contents="""
       sid,50
       jair,30
       ariana,20
       """)
    with open('abe/price.txt') as f:
        assert f.read() == "10"
    process_payments_and_record_updates()
    with open('./abe/transactions.txt') as f:
        assert f.read() == ""


@time_machine.travel(datetime(1985, 10, 26, 1, 24), tick=False)
@patch('oldabe.money_in.get_git_revision_short_hash', return_value='abcd123')
def test_creates_transactions_on_payment(mock_git_rev, fs):
    fs.create_file("./abe/price.txt", contents="10")
    fs.create_file("./abe/valuation.txt", contents="100000")
    fs.create_file("./abe/instruments.txt", contents="""
        old abe,1
        DIA,5
        """)
    fs.create_file("./abe/attributions.txt", contents="""
       sid,50
       jair,30
       ariana,20
       """)

    fs.create_file("./abe/payments/1.txt",
                   contents="sam,036eaf6,100,dummydate")
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

