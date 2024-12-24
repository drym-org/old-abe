from decimal import Decimal
from oldabe.models import ItemizedPayment, Debt, Advance
import pytest


@pytest.fixture
def instruments():
    return {
        'old_abe': Decimal("0.01"),
        'dia': Decimal("0.05"),
    }


@pytest.fixture
def normalized_attributions():
    return {
        'a@b.com': Decimal("0.2"),
        'b@c.com': Decimal("0.8"),
    }


@pytest.fixture
def excess_attributions():
    return {
        'a@b.com': Decimal("0.2"),
        'b@c.com': Decimal("0.9"),
    }


@pytest.fixture
def shortfall_attributions():
    return {
        'a@b.com': Decimal("0.2"),
        'b@c.com': Decimal("0.7"),
    }


@pytest.fixture
def empty_attributions():
    return {}


@pytest.fixture
def single_contributor_attributions():
    return {'a@b.com': Decimal("1")}


@pytest.fixture
def itemized_payments():
    data = [
        ['a@b.com', '6', '94', 'payment-1.txt'],
        ['a@b.com', '2', '20', 'payment-2.txt'],
        ['c@d.com', '1', '10', 'payment-3.txt'],
    ]
    return [
        ItemizedPayment(ip[0], Decimal(ip[1]), Decimal(ip[2]), True, ip[3])
        for index, ip in enumerate(data)
    ]


@pytest.fixture
def new_itemized_payments():
    return [
        ItemizedPayment(
            'a@b.com', Decimal('4'), Decimal('80'), True, 'payment-4.txt'
        ),
        ItemizedPayment(
            'c@d.com', Decimal('5'), Decimal('20'), True, 'payment-5.txt'
        ),
        ItemizedPayment(
            'c@d.com', Decimal('10'), Decimal('90'), False, 'payment-6.txt'
        ),
    ]


@pytest.fixture
def fresh_debts():
    return [
        Debt('a@b.com', Decimal('10'), Decimal('0'), 'payment-10.txt'),
        Debt('a@b.com', Decimal('40'), Decimal('0'), 'payment-10.txt'),
    ]

@pytest.fixture
def negative_advances():
    return [
        Advance('a@b.com', Decimal('-20'), 'payment-10.txt'),
        Advance('a@b.com', Decimal('-30'), 'payment-10.txt'),
    ]
