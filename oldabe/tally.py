from decimal import Decimal
from collections import defaultdict
from operator import sub


# TODO: needs tests
class Tally(defaultdict[str, Decimal]):
    """
    A dictionary for keeping the tally of an amount

    Inspired by collections.Counter, but instead of a count of occurrences it
    keeps the sum of an amount.
    """

    def __init__(self, source=[]):
        if type(source) is dict:
            super().__init__(Decimal, source)
            return

        super().__init__(Decimal)
        for key, amount in source:
            self[key] += amount

    def combine(self, combinator, other):
        result = Tally()
        for key in dict(**self, **other).keys():
            result[key] = combinator(self[key], other[key])
        return result

    def __sub__(self, other):
        return self.combine(sub, other)
