from typing import Callable, Union

from sims.sim_info import SimInfo

from s4f_base_classes import SimFilter, SimTransformer


class Logic:
    @staticmethod
    def conjunction(*filters: Callable[[SimInfo], bool]) -> SimFilter:
        class ConjunctiveFilter(SimFilter):
            def __call__(self, sim: SimInfo) -> bool:
                return all(f(sim) for f in filters)

        return ConjunctiveFilter()

    @staticmethod
    def disjunction(*filters: Callable[[SimInfo], bool]) -> SimFilter:
        class DisjunctiveFilter(SimFilter):
            def __call__(self, sim: SimInfo) -> bool:
                return any(f(sim) for f in filters)

        return DisjunctiveFilter()

    @staticmethod
    def negation(filter_x: Callable[[SimInfo], bool]) -> SimFilter:
        class NegationFilter(SimFilter):
            def __call__(self, sim: SimInfo) -> bool:
                return not filter_x(sim)

        return NegationFilter()

    @staticmethod
    def compose_filter(
        filter_x: Callable[[SimInfo], bool], transformer: Callable[[SimInfo], SimInfo]
    ) -> SimFilter:
        class ComposedFilter(SimFilter):
            def __call__(self, sim: SimInfo) -> bool:
                try:
                    transformed_sim = transformer(sim)
                    if transformed_sim is None:
                        return False
                    return filter_x(transformed_sim)
                except Exception:
                    return False

        return ComposedFilter()

    @staticmethod
    def compose_transformer(
        *transformers: Callable[[SimInfo], SimInfo],
    ) -> SimTransformer:
        class ComposedTransformer(SimTransformer):
            def __call__(self, sim: SimInfo) -> Union[SimInfo, None]:
                try:
                    transformed_sim = sim
                    for transformer in transformers:
                        transformed_sim = transformer(transformed_sim)
                        if transformed_sim is None:
                            return None
                    return transformed_sim
                except Exception:
                    return None

        return ComposedTransformer()
