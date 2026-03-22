from typing import Callable, List, Union

from s4f_base_classes import SimFilter, SimTransformer
from s4f_logic import Logic


class TinyParser:
    def __init__(
        self,
        tokens: List[str],
        token_parser: Callable[[str], Union[SimFilter, SimTransformer]],
    ):
        self._tokens = [token.strip().lower() for token in tokens]
        self.token_parser = token_parser

    def parse(self) -> SimFilter:
        filters: List[Union[SimFilter, SimTransformer]] = []
        for idx, token in enumerate(self._tokens):
            if token == "and":
                filt_x = filters.pop()
                filt_y = filters.pop()
                # if not isinstance(filt_x, SimFilter) or not isinstance(
                #     filt_y, SimFilter
                # ):
                #     raise ValueError(
                #         "Invalid filter expression: {}".format(self._tokens)
                #     )
                filters.append(Logic.conjunction(filt_x, filt_y))  # pyright: ignore[reportArgumentType]
            elif token == "or":
                filt_y = filters.pop()
                filt_x = filters.pop()
                # if not isinstance(filt_x, SimFilter) or not isinstance(
                #     filt_y, SimFilter
                # ):
                #     raise ValueError(
                #         "Invalid filter expression: {}".format(self._tokens)
                #     )
                filters.append(Logic.disjunction(filt_x, filt_y))  # pyright: ignore[reportArgumentType]
            elif token == "not":
                filt_x = filters.pop()
                # if not isinstance(filt_x, SimFilter):
                #     raise ValueError(
                #         "Invalid filter expression: {}".format(self._tokens)
                #     )
                filters.append(Logic.negation(filt_x))  # pyright: ignore[reportArgumentType]
            elif token == "compose_filter":
                filt_x = filters.pop()
                transformer = filters.pop()
                # if not isinstance(filt_x, SimFilter) or not isinstance(
                #     transformer, SimTransformer
                # ):
                #     raise ValueError(
                #         "Invalid filter expression: {} - filt_x:{}:{} - transformer:{}:{}".format(
                #             self._tokens,
                #             filt_x,
                #             isinstance(filt_x, SimFilter),
                #             transformer,
                #             isinstance(transformer, SimTransformer),
                #         )
                #     )
                filters.append(Logic.compose_filter(filt_x, transformer))  # pyright: ignore[reportArgumentType]
            elif token == "compose_transformer":
                transformer_x = filters.pop()
                transformer_y = filters.pop()
                # if not isinstance(transformer_x, SimTransformer) or not isinstance(
                #     transformer_y, SimTransformer
                # ):
                #     raise ValueError(
                #         "Invalid filter expression: {}".format(self._tokens)
                #     )
                filters.append(
                    Logic.compose_transformer(transformer_x, transformer_y)  # pyright: ignore[reportArgumentType]
                )
            else:
                atom = self.token_parser(token)
                filters.append(atom)
        if len(filters) != 1:
            raise ValueError(
                "Invalid filter expression: {} - {}".format(self._tokens, filters)
            )
        # if not isinstance(filters[0], SimFilter):
        #     raise ValueError(
        #         "Invalid filter expression: {} - {}".format(self._tokens, filters)
        #     )
        return filters[0]  # pyright: ignore[reportReturnType]
