from decimal import Decimal
from typing import Set


class Distribution(dict["str | None", Decimal]):
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
            {
                shareholder: share * (Decimal("1") / total)
                for shareholder, share in self.items()
            }
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
        return {
            shareholder: amount * share
            for shareholder, share in self._normalized().items()
            if shareholder is not None
        }
