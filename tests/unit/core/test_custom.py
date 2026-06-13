"""Unit tests for ORM-neutral custom predicate definitions."""

from __future__ import annotations

from pyrsql.core.custom import CustomPredicateDefinition
from pyrsql.parsing.operators import ComparisonOperator


def test_custom_predicate_definition_stores_valid_runtime_contract() -> None:
    """Preserves the configured operator and argument type."""
    definition = CustomPredicateDefinition(
        operator=ComparisonOperator(
            name="all_match",
            spellings=("=all=",),
            minimum_arguments=1,
            maximum_arguments=1,
        ),
        argument_type=str,
    )

    assert definition.operator.name == "all_match"
    assert definition.argument_type is str
