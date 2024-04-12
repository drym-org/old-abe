import pytest
from unittest.mock import patch
from oldabe.money_in import (
    process_payments_and_record_updates,
)
import os


@patch('oldabe.money_in.get_git_revision_short_hash', return_value='abcd123')
def test_creates_transactions_on_payment(mock_git_rev, fs):
    ff = fs.create_file("./abe/price.txt", contents="10")
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
    # print(ff.name)
    # print(ff.contents)
    # print(ff.filesystem)
    with open('abe/price.txt') as f:
        assert f.read() == "10"
    process_payments_and_record_updates()
    with open('./abe/transactions.txt') as f:
        assert 'sid' in f.read()
        assert 'jair' in f.read()
        assert 'ariana' in f.read()
