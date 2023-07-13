from decimal import Decimal
from oldabe.models import ItemizedPayment
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
    data = [
        ['a@b.com', '4', '80', 'payment-4.txt'],
        ['d@e.com', '10', '90', 'payment-5.txt'],
    ]
    return [
        ItemizedPayment(ip[0], Decimal(ip[1]), Decimal(ip[2]), True, ip[3])
        for index, ip in enumerate(data)
    ]
