"""Shared query options."""

from dataclasses import dataclass
from dataclasses import field


@dataclass(frozen=True, slots=True)
class QueryOptions:
    """Backend-neutral query options."""

    strict_equality: bool = False
    max_expression_depth: int = 16
    max_arguments_per_operator: int = 100
    field_mapping: dict[str, str] = field(default_factory=dict)
