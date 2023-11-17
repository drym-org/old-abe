from datetime import datetime
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Transaction:
    email: str = None
    amount: Decimal = 0
    payment_file: str = None
    commit_hash: str = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Debt:
    email: str = None
    amount: Decimal = None
    # amount_paid is a running tally of how much of this debt has been paid
    # in future will link to Transaction objects instead
    amount_paid: Decimal = 0
    payment_file: str = None
    commit_hash: str = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def key(self):
        return (self.email, self.payment_file)

    def is_fulfilled(self):
        return self.amount_paid == self.amount

    def amount_remaining(self):
        return self.amount - self.amount_paid


@dataclass
class Advance:
    pass


@dataclass
class Payment:
    email: str = None
    amount: Decimal = 0
    attributable: bool = True
    file: str = None


# ItemizedPayment acts as a proxy for a Payment object that keeps track
# of how much of the original payment is owed to instruments and how much
# is owed to directly to the project (attributions.txt). This allows us to
# avoid mutating Payment records.
@dataclass
class ItemizedPayment:
    email: str = None
    fee_amount: Decimal = 0  # instruments
    project_amount: Decimal = 0  # attributions
    attributable: bool = True
    payment_file: str = (
        None  # acts like a foreign key to original payment object
    )


@dataclass
class Attribution:
    email: str = None
    share: Decimal = 0
    dilutable: bool = True
