from decimal import Decimal
from fractions import Fraction
from typing import Set


def fraction_to_decimal(f):
    """Convert a Fraction to a Decimal."""
    return Decimal(f.numerator) / Decimal(f.denominator)


class Distribution(dict["str | None", Fraction]):
    """
    A dictionary of shareholders to proportions

    None can be used as a shareholder to omit a percentage from distribution
    and enumeration.
    """

    def _normalized(self) -> "Distribution":
        """
        Return a distribution with the same proportions that adds up to 1
        """
        total = sum(self.values())

        return Distribution(
            {shareholder: share / total for shareholder, share in self.items()}
        )

    def without(self, exclude: Set[str]) -> "Distribution":
        """
        Return a distribution without the shareholders in exclude

        Other shareholders retain their relative proportions.
        """
        return Distribution(
            {
                shareholder: share
                for shareholder, share in self.items()
                if shareholder not in exclude
            }
        )

    def distribute(self, amount: Decimal) -> dict[str, Decimal]:
        """
        Distribute an amount amongst shareholders
        """
        amounts = {
            shareholder: round(amount * fraction_to_decimal(share), 2)
            for shareholder, share in self._normalized().items()
        }
        total = sum(amounts.values())
        difference = total - amount
        if difference != 0:
            _, recipient = sorted(
                (-amount, shareholder)
                for shareholder, amount in amounts.items()
            )[0]
            amounts[recipient] -= difference
        return {
            shareholder: amount
            for shareholder, amount in amounts.items()
            if shareholder is not None
        }
