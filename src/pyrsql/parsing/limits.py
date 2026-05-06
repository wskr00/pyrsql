"""Safety limits for lexing and parsing."""

import msgspec


class ParseLimits(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Configurable safety limits for query processing."""

    max_query_length: int = 4096
    max_selector_length: int = 256
    max_argument_length: int = 1024
    max_arguments_per_list: int = 100
    max_expression_depth: int = 16
    max_node_count: int = 1024

    def __post_init__(self) -> None:
        """Validates parser limit invariants."""
        if self.max_query_length <= 0:
            raise ValueError("max_query_length must be greater than 0.")
        if self.max_selector_length <= 0:
            raise ValueError("max_selector_length must be greater than 0.")
        if self.max_argument_length <= 0:
            raise ValueError("max_argument_length must be greater than 0.")
        if self.max_arguments_per_list <= 0:
            raise ValueError(
                "max_arguments_per_list must be greater than 0."
            )
        if self.max_expression_depth <= 0:
            raise ValueError("max_expression_depth must be greater than 0.")
        if self.max_node_count <= 0:
            raise ValueError("max_node_count must be greater than 0.")


DEFAULT_PARSE_LIMITS = ParseLimits()
