"""Sanity tests for the package-level public API."""

import pytest

import pyrsql
from pyrsql.core.custom import CustomPredicateDefinition
from pyrsql.core.options import QueryOptions
from pyrsql.parsing.operators import ComparisonOperator
from pyrsql.parsing.operators import DEFAULT_OPERATOR_REGISTRY
from pyrsql.parsing.operators import OperatorRegistry


def test_parse_returns_query_object() -> None:
    """Ensures the package-level parse helper builds a query object."""
    query = pyrsql.parse("name==demo")
    assert query.text == "name==demo"
    assert query.options.strict_equality is False
    assert query.expression is not None
    assert query.semantic_expression is not None


def test_parse_uses_custom_operator_registry() -> None:
    """Ensures package parsing honors custom operator configuration."""
    all_match = ComparisonOperator(
        name="all_match",
        spellings=("=all=",),
        minimum_arguments=1,
        maximum_arguments=1,
    )
    options = QueryOptions(
        operator_registry=OperatorRegistry(
            operators=DEFAULT_OPERATOR_REGISTRY.operators + (all_match,)
        )
    )
    query = pyrsql.parse("name=all=demo", options=options)
    assert query.expression is not None
    assert query.expression.operator.name == "all_match"


def test_parse_uses_custom_predicate_definition() -> None:
    """Ensures custom predicates extend the operator registry automatically."""
    all_match = ComparisonOperator(
        name="all_match",
        spellings=("=all=",),
        minimum_arguments=1,
        maximum_arguments=1,
    )
    options = QueryOptions(
        custom_predicates={
            "all_match": CustomPredicateDefinition(
                operator=all_match,
                argument_type=str,
            )
        }
    )
    query = pyrsql.parse("name=all=demo", options=options)
    assert query.expression is not None
    assert query.expression.operator.name == "all_match"


def test_query_options_reject_mismatched_custom_predicate_key() -> None:
    """Rejects custom predicate definitions keyed by the wrong name."""
    with pytest.raises(ValueError):
        QueryOptions(
            custom_predicates={
                "wrong_name": CustomPredicateDefinition(
                    operator=ComparisonOperator(
                        name="all_match",
                        spellings=("=all=",),
                        minimum_arguments=1,
                        maximum_arguments=1,
                    ),
                    argument_type=str,
                )
            }
        )
