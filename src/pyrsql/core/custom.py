"""Backend-neutral custom predicate definitions."""

from dataclasses import dataclass
from typing import Any

from pyrsql.parsing.operators import ComparisonOperator


@dataclass(frozen=True, slots=True)
class CustomPredicateDefinition:
    """Defines a custom predicate independently of any backend."""

    operator: ComparisonOperator
    argument_type: type[Any]
