from oldabe.repos import FileRepo
from decimal import Decimal
from dataclasses import dataclass, field


@dataclass
class TestModel:
    field1: str
    field2: Decimal
    optional_field: str = field(default="")


class TestModelRepo(FileRepo):
    filename = "testmodels.txt"
    Model = TestModel


class TestFileRepo:

    def test_all_fields_present(self, fs):
        fs.create_file("testmodels.txt", contents="blah,42,blah?")
        assert list(TestModelRepo()) == [TestModel("blah", 42, "blah?")]

    def test_missing_field(self, fs):
        fs.create_file("testmodels.txt", contents="blah,42")
        assert list(TestModelRepo()) == [TestModel("blah", 42)]
