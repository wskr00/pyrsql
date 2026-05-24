"""Unit tests for ORM-neutral custom predicate definitions."""

from __future__ import annotations

import pytest

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


@pytest.mark.parametrize(
    ("kwargs", "pattern"),
    [
        pytest.param(
            {"operator": object(), "argument_type": str},
            "ComparisonOperator",
            id="invalid-operator",
        ),
        pytest.param(
            {
                "operator": ComparisonOperator(
                    name="all_match",
                    spellings=("=all=",),
                    minimum_arguments=1,
                    maximum_arguments=1,
                ),
                "argument_type": "str",
            },
            "runtime type",
            id="invalid-argument-type",
        ),
    ],
)
def test_custom_predicate_definition_rejects_invalid_runtime_contract(
    kwargs: dict[str, object],
    pattern: str,
) -> None:
    """Rejects invalid custom predicate contract inputs."""
    with pytest.raises(TypeError, match=pattern):
        CustomPredicateDefinition(**kwargs)
