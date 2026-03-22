import enum
from typing import Union

from sims.sim_info import SimInfo


class SimFilterKeyword(enum.IntEnum):
    EQUALS = 1
    GREATER_THAN = 2
    LESS_THAN = 3
    CONTAINS = 4


class SimFilter:
    """
    A base class for all filters.
    """

    def __init__(self):
        return

    def __call__(self, sim: SimInfo) -> bool:
        raise NotImplementedError(
            "Filter is an abstract base class and cannot be called directly."
        )

    def __and__(self, other: "SimFilter") -> "SimFilter":
        class CombinedSimFilter(SimFilter):
            def __call__(self, sim: SimInfo) -> bool:
                return self(sim) and other(sim)

        return CombinedSimFilter()

    def __or__(self, other: "SimFilter") -> "SimFilter":
        class CombinedSimFilter(SimFilter):
            def __call__(self, sim: SimInfo) -> bool:
                return self(sim) or other(sim)

        return CombinedSimFilter()

    def __invert__(self) -> "SimFilter":
        class NegatedSimFilter(SimFilter):
            def __call__(self, sim: SimInfo) -> bool:
                return not self(sim)

        return NegatedSimFilter()


class SimTransformer:
    def __call__(self, sim: SimInfo) -> Union[SimInfo, None]:
        raise NotImplementedError(
            "SimTransformer is an abstract base class and cannot be called directly."
        )
