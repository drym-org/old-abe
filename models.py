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
