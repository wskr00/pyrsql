"""Safety limits for lexing and parsing."""

from __future__ import annotations

import msgspec

from pyrsql._validation import validate_positive_int


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
        validate_positive_int(
            self.max_query_length,
            field_name="max_query_length",
        )
        validate_positive_int(
            self.max_selector_length,
            field_name="max_selector_length",
        )
        validate_positive_int(
            self.max_argument_length,
            field_name="max_argument_length",
        )
        validate_positive_int(
            self.max_arguments_per_list,
            field_name="max_arguments_per_list",
        )
        validate_positive_int(
            self.max_expression_depth,
            field_name="max_expression_depth",
        )
        validate_positive_int(
            self.max_node_count,
            field_name="max_node_count",
        )


DEFAULT_PARSE_LIMITS = ParseLimits()
