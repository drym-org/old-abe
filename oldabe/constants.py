import os
from decimal import Decimal

ACCOUNTING_ZERO = Decimal("0.01")

ABE_ROOT = './abe'
PAYOUTS_DIR = os.path.join(ABE_ROOT, 'payouts')
PAYMENTS_DIR = os.path.join(ABE_ROOT, 'payments')
NONATTRIBUTABLE_PAYMENTS_DIR = os.path.join(
    ABE_ROOT, 'payments', 'nonattributable'
)

TRANSACTIONS_FILE = os.path.join(ABE_ROOT, 'transactions.txt')
DEBTS_FILE = os.path.join(ABE_ROOT, 'debts.txt')
ADVANCES_FILE = os.path.join(ABE_ROOT, 'advances.txt')
UNPAYABLE_CONTRIBUTORS_FILE = os.path.join(ABE_ROOT, 'unpayable_contributors.txt')
ITEMIZED_PAYMENTS_FILE = os.path.join(ABE_ROOT, 'itemized_payments.txt')
PRICE_FILE = os.path.join(ABE_ROOT, 'price.txt')
VALUATION_FILE = os.path.join(ABE_ROOT, 'valuation.txt')
ATTRIBUTIONS_FILE = os.path.join(ABE_ROOT, 'attributions.txt')
INSTRUMENTS_FILE = os.path.join(ABE_ROOT, 'instruments.txt')
