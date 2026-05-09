"""ORM-neutral custom predicate definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import msgspec

if TYPE_CHECKING:
    from pyrsql.parsing.operators import ComparisonOperator


class CustomPredicateDefinition(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
):
    """Defines a custom predicate independently of any orm."""

    operator: ComparisonOperator
    argument_type: type[Any]
