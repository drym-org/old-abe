import os

ABE_ROOT = 'abe'
PAYOUTS_DIR = os.path.join(ABE_ROOT, 'payouts')
PAYMENTS_DIR = os.path.join(ABE_ROOT, 'payments')
NONATTRIBUTABLE_PAYMENTS_DIR = os.path.join(
    ABE_ROOT, 'payments', 'nonattributable'
)

TRANSACTIONS_FILE = os.path.join(ABE_ROOT, 'transactions.txt')
DEBTS_FILE = os.path.join(ABE_ROOT, 'debts.txt')
ADVANCES_FILE = os.path.join(ABE_ROOT, 'advances.txt')
UNPAYABLE_CONTRIBUTORS_FILE = 'unpayable_contributors.txt'
ITEMIZED_PAYMENTS_FILE = 'itemized_payments.txt'
PRICE_FILE = 'price.txt'
VALUATION_FILE = 'valuation.txt'
ATTRIBUTIONS_FILE = 'attributions.txt'
INSTRUMENTS_FILE = 'instruments.txt'
