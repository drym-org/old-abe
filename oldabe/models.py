from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from fractions import Fraction

from oldabe.git import get_git_revision_short_hash


# Wrapping so that tests can mock it
def default_commit_hash():
    return get_git_revision_short_hash()


@dataclass
class Transaction:
    email: str
    amount: Decimal
    payment_file: str
    commit_hash: str = field(default_factory=lambda: default_commit_hash())
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Payout:
    name: str
    email: str
    amount: Decimal
    created_at: datetime = field(default_factory=datetime.utcnow)
    memo: str = field(default="")


@dataclass
class Debt:
    email: str
    amount: Decimal
    payment_file: str
    commit_hash: str = field(default_factory=lambda: default_commit_hash())
    # This created date is just for reference for any admins
    # but we don't need to check it anywhere since all debts for a particular
    # payment are created together, and any subsequent payments giving rise
    # to fresh debts would simply append to this debts file, and the
    # chronological order would be implicit.
    created_at: datetime = field(default_factory=datetime.utcnow)


# Individual advances can have a positive or negative amount (to
# indicate an actual advance payment, or a drawn down advance).
# To find the current advance amount for a given contributor,
# sum all of their existing Advance objects.
@dataclass
class Advance:
    email: str
    amount: Decimal
    payment_file: str
    commit_hash: str = field(default_factory=lambda: default_commit_hash())
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Payment:
    email: str
    name: str
    amount: Decimal
    # Should move this, but it will invalidate existing files
    created_at: datetime = field(default_factory=datetime.utcnow)
    attributable: bool = True
    file: str = ''


# ItemizedPayment acts as a proxy for a Payment object that keeps track
# of how much of the original payment is owed to instruments and how much
# is owed to directly to the project (attributions.txt). This allows us to
# avoid mutating Payment records.
@dataclass
class ItemizedPayment:
    email: str
    fee_amount: Decimal  # instruments
    project_amount: Decimal  # attributions
    attributable: bool
    payment_file: str  # acts like a foreign key to original payment object


@dataclass
class Attribution:
    email: str
    share: Fraction
