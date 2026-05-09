"""ORM-neutral custom predicate definitions."""

from typing import Any

import msgspec

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
