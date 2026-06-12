"""ORM-neutral custom predicate definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import msgspec

if TYPE_CHECKING:
    from pyrsql.parsing.operators import ComparisonOperator

ArgumentType = type[Any]


class CustomPredicateDefinition(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
):
    """Defines one ORM-neutral custom predicate contract.

    Attributes:
        operator: The query-language operator exposed to users.
        argument_type: Runtime type used to coerce raw predicate arguments
            before backend-specific lowering.
    """

    operator: ComparisonOperator
    argument_type: ArgumentType
