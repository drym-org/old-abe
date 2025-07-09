from oldabe.distribution import Distribution
from fractions import Fraction
from decimal import Decimal


class TestDistribute:

    def test_distributes_whole_amount(self):
        amount = 100
        distribution = Distribution(
            {
                'sid': Fraction(5, 10),
                'jair': Fraction(3, 10),
                'ariana': Fraction(2, 10),
            }
        )
        assert distribution.distribute(amount) == {
            'sid': 50,
            'jair': 30,
            'ariana': 20,
        }

    def test_distributes_excess_dust(self):
        amount = 100
        distribution = Distribution(
            {
                'sid': Fraction(1, 6),
                'jair': Fraction(1, 6),
                'ariana': Fraction(2, 3),
            }
        )
        assert distribution.distribute(amount) == {
            'sid': Decimal('16.67'),
            'jair': Decimal('16.67'),
            'ariana': Decimal('66.66'),
        }
