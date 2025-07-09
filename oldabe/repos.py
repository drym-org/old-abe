import csv
import dataclasses
import os
import re
from datetime import datetime
from decimal import Decimal
from typing import Any, Generic, Iterable, Iterator, List, Type, TypeVar
from fractions import Fraction

from oldabe.constants import (
    ADVANCES_FILE,
    ATTRIBUTIONS_FILE,
    DEBTS_FILE,
    INSTRUMENTS_FILE,
    ITEMIZED_PAYMENTS_FILE,
    NONATTRIBUTABLE_PAYMENTS_DIR,
    PAYMENTS_DIR,
    PAYOUTS_DIR,
    TRANSACTIONS_FILE,
    UNPAYABLE_CONTRIBUTORS_FILE,
)
from oldabe.models import (
    Advance,
    Attribution,
    Debt,
    ItemizedPayment,
    Payment,
    Payout,
    Transaction,
)


def fix_types(row: List[str], Model: type) -> List[Any]:
    """
    Cast string field values from the CSV into the proper types
    """

    def _cast(field, value):
        if field.type is Decimal:
            return Decimal(re.sub("[^0-9.]", "", value))
        elif field.type is Fraction:
            return Fraction(value)
        elif field.type is datetime:
            return datetime.fromisoformat(value)
        else:
            return value

    return [
        _cast(field, value)
        for field, value in zip(dataclasses.fields(Model), row)
    ]


T = TypeVar('T')


class FileRepo(Generic[T]):
    """
    A sequence of dataclass instances stored as rows in a CSV
    """

    filename: str
    Model: Type[T]

    def __iter__(self) -> Iterator[T]:
        objs = []
        try:
            with open(self.filename) as f:
                for row in csv.reader(f, skipinitialspace=True):
                    if dataclasses.is_dataclass(self.Model):
                        row = fix_types(row, self.Model)
                    obj = self.Model(*row)
                    objs.append(obj)
        except FileNotFoundError:
            pass

        yield from objs

    def extend(self, objs: Iterable[T]):
        with open(self.filename, "a") as f:
            writer = csv.writer(f)
            for obj in objs:
                writer.writerow(dataclasses.astuple(obj))


class DirRepo(Generic[T]):
    """
    A sequence of dataclass instances stored as single row CSV files in a dir
    """

    dirname: str
    Model: Type[T]

    def __iter__(self) -> Iterator[T]:
        objs = []
        try:
            filenames = [
                f
                for f in os.listdir(self.dirname)
                if not os.path.isdir(os.path.join(self.dirname, f))
            ]
        except FileNotFoundError:
            filenames = []

        for filename in filenames:
            with open(os.path.join(self.dirname, filename)) as f:
                row = next(csv.reader(f, skipinitialspace=True))
                if dataclasses.is_dataclass(self.Model):
                    row = fix_types(row, self.Model)
                obj = self.Model(*row)
                setattr(obj, "file", filename)
                objs.append(obj)

        yield from objs


class TransactionsRepo(FileRepo[Transaction]):
    filename = TRANSACTIONS_FILE
    Model = Transaction


class PayoutsRepo(DirRepo):
    dirname = PAYOUTS_DIR
    Model = Payout


class DebtsRepo(FileRepo[Debt]):
    filename = DEBTS_FILE
    Model = Debt


class AdvancesRepo(FileRepo[Advance]):
    filename = ADVANCES_FILE
    Model = Advance


class AttributionsRepo(FileRepo[Attribution]):
    filename = ATTRIBUTIONS_FILE
    Model = Attribution


class InstrumentsRepo(FileRepo[Attribution]):
    filename = INSTRUMENTS_FILE
    Model = Attribution


class AttributablePaymentsRepo(DirRepo[Payment]):
    dirname = PAYMENTS_DIR
    Model = Payment

    def __iter__(self):
        yield from (
            dataclasses.replace(obj, attributable=True)
            for obj in super().__iter__()
        )


class NonAttributablePaymentsRepo(DirRepo[Payment]):
    dirname = NONATTRIBUTABLE_PAYMENTS_DIR
    Model = Payment

    def __iter__(self):
        yield from (
            dataclasses.replace(obj, attributable=False)
            for obj in super().__iter__()
        )


class AllPaymentsRepo:
    def __iter__(self):
        yield from AttributablePaymentsRepo()
        yield from NonAttributablePaymentsRepo()


class ItemizedPaymentsRepo(FileRepo[ItemizedPayment]):
    filename = ITEMIZED_PAYMENTS_FILE
    Model = ItemizedPayment


class UnpayableContributorsRepo(FileRepo[str]):
    filename = UNPAYABLE_CONTRIBUTORS_FILE
    Model = str
