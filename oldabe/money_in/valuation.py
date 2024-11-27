import csv
import re
from ..constants import (
    VALUATION_FILE,
)
from decimal import Decimal


# note that commas are used as a decimal separator in some languages
# (e.g. Spain Spanish), so that would need to be handled at some point
def read_valuation() -> Decimal:
    with open(VALUATION_FILE) as f:
        valuation = f.readline()
        valuation = Decimal(re.sub("[^0-9.]", "", valuation))
        return valuation


def write_valuation(valuation):
    rounded_valuation = f"{valuation:.2f}"
    with open(VALUATION_FILE, "w") as f:
        writer = csv.writer(f)
        writer.writerow((rounded_valuation,))
