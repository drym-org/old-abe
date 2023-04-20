from datetime import datetime
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Transaction:
    email: str = None
    amount: Decimal = None
    payment_file: str = None
    commit_hash: str = None
    created_at: datetime = field(default_factory=datetime.utcnow)


class Debt:
    email: str = None
    amount: Decimal = None
    # amount_paid is a running tally of how much of this debt has been paid
    # in future will link to Transaction objects instead
    amount_paid: Decimal = 0
    payment_file: str = None
    commit_hash: str = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Payment:
    email: str = None
    amount: Decimal = None
    attributable: bool = True
    file: str = None
