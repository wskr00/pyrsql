"""ORM-neutral custom predicate definitions."""

from __future__ import annotations

from typing import Any

import msgspec

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

    def __post_init__(self) -> None:
        """Validates custom predicate invariants.

        Raises:
            TypeError: If the operator or argument type has the wrong runtime
                type.
        """
        if not isinstance(self.operator, ComparisonOperator):
            raise TypeError(
                "operator must be a ComparisonOperator instance.",
            )
        if not isinstance(self.argument_type, type):
            raise TypeError("argument_type must be a runtime type.")
