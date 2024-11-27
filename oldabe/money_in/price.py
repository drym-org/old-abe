import re
from ..constants import (
    PRICE_FILE,
)
from decimal import Decimal


def read_price() -> Decimal:
    with open(PRICE_FILE) as f:
        price = f.readline()
        price = Decimal(re.sub("[^0-9.]", "", price))
        return price
