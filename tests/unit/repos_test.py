from oldabe.repos import FileRepo, DirRepo
from decimal import Decimal
import decimal
from dataclasses import dataclass, field
from datetime import datetime
from fractions import Fraction
import os

import pytest


@dataclass
class MyTestModel:
    field1: str
    field2: Decimal
    field3: Fraction
    created_at: datetime
    optional_field: str = field(default="")


class MyTestModelRepo(FileRepo):
    filename = "testmodels.txt"
    Model = MyTestModel


class MyTestDirModelRepo(DirRepo):
    dirname = "testdir"
    Model = MyTestModel


class TestFileRepo:

    # Note that valid CSV files have to have trailing newlines,
    # but with only one row in a test, it doesn't matter
    # We could potentially make a csv_fs fixture to do it uniformly
    def test_all_fields_present(self, fs):
        fs.create_file("testmodels.txt", contents="blah,42,1/3,2025-01-12,blah?")
        assert list(MyTestModelRepo()) == [MyTestModel("blah", 42, Fraction(1, 3), datetime(2025, 1, 12), "blah?")]

    def test_missing_field(self, fs):
        fs.create_file("testmodels.txt", contents="blah,42,1/3,2025-01-12")
        assert list(MyTestModelRepo()) == [MyTestModel("blah", 42, Fraction(1, 3), datetime(2025, 1, 12))]

    def test_invalid_type(self, fs):
        fs.create_file("testmodels.txt", contents="blah,not-decimal,1/3,2025-01-12,blah?")
        with pytest.raises(decimal.InvalidOperation):
            list(MyTestModelRepo())

    def test_add_new_rows(self, fs):
        fs.create_file("testmodels.txt", contents="blah,42,1/3,2025-01-12,blah?\n")
        repo = MyTestModelRepo()
        repo.extend([MyTestModel("blah too", 42, Fraction(1, 3), datetime(2025, 1, 12), "also blah?")])
        assert list(MyTestModelRepo()) == [MyTestModel("blah", 42, Fraction(1, 3), datetime(2025, 1, 12), "blah?"),
                                           MyTestModel("blah too", 42, Fraction(1, 3), datetime(2025, 1, 12), "also blah?")]

    def test_empty_file(self, fs):
        fs.create_file("testmodels.txt", contents="")
        assert list(MyTestModelRepo()) == []

    def test_file_with_multiple_lines(self, fs):
        fs.create_file("testmodels.txt", contents="blah,42,1/3,2025-01-12,blah?\nblah too,42,1/3,2025-01-12,also blah?\n")
        assert list(MyTestModelRepo()) == [MyTestModel("blah", 42, Fraction(1, 3), datetime(2025, 1, 12), "blah?"),
                                           MyTestModel("blah too", 42, Fraction(1, 3), datetime(2025, 1, 12), "also blah?")]


class TestDirRepo:

    def test_missing_dir(self, fs):
        assert not os.path.isdir("testdir")
        # if the client repo doesn't have any payments yet,
        # it's more convenient to just return an empty list
        # than to raise an error indicating bad folder schema
        assert list(MyTestDirModelRepo()) == []

    def test_empty_dir(self, fs):
        fs.create_dir("testdir")
        assert list(MyTestDirModelRepo()) == []

    def test_single_file(self, fs):
        fs.create_file("testdir/testmodel.txt", contents="blah,42,1/3,2025-01-12,blah?\n")
        assert list(MyTestDirModelRepo()) == [MyTestModel("blah", 42, Fraction(1, 3), datetime(2025, 1, 12), "blah?")]

    def test_multiple_files(self, fs):
        fs.create_file("testdir/testmodel1.txt", contents="blah,42,1/3,2025-01-12,blah?\n")
        fs.create_file("testdir/testmodel2.txt", contents="blah too,42,1/3,2025-01-12,also blah?\n")
        assert list(MyTestDirModelRepo()) == [MyTestModel("blah", 42, Fraction(1, 3), datetime(2025, 1, 12), "blah?"),
                                              MyTestModel("blah too", 42, Fraction(1, 3), datetime(2025, 1, 12), "also blah?")]
