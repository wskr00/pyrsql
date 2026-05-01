"""Shared query options."""

from dataclasses import dataclass
from dataclasses import field

from pyrsql.parsing.limits import ParseLimits


@dataclass(frozen=True, slots=True)
class QueryOptions:
    """Backend-neutral query options."""

    strict_equality: bool = False
    field_mapping: dict[str, str] = field(default_factory=dict)
    parse_limits: ParseLimits = field(default_factory=ParseLimits)
