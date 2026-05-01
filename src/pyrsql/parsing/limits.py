"""Safety limits for lexing and parsing."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ParseLimits:
    """Configurable safety limits for query processing."""

    max_query_length: int = 4096
    max_selector_length: int = 256
    max_argument_length: int = 1024
    max_arguments_per_list: int = 100
    max_expression_depth: int = 16
    max_node_count: int = 1024
