"""Functional tests for the package-level public API."""

import pytest

import pyrsql
from pyrsql.core.compiler import CompilationResult
from pyrsql.core.custom import CustomPredicateDefinition
from pyrsql.core.options import QueryOptions
from pyrsql.core.page import PageRequest
from pyrsql.core.query import Query
from pyrsql.core.sort import Sort
from pyrsql.orms.base import ORM
from pyrsql.parsing.operators import (
    DEFAULT_OPERATOR_REGISTRY,
    ComparisonOperator,
    OperatorRegistry,
)

pytestmark = [pytest.mark.functional]


class _CompiledQuery:
    """Minimal compiled query fake for public API tests."""

    def apply(
        self,
        target: object,
        model: type[object],
    ) -> tuple[object, type[object]]:
        """Returns the received target and model."""
        return target, model


class _ORM(ORM):
    """Minimal ORM fake for public API tests."""

    name = "fake-orm"

    def __init__(self) -> None:
        self.last_query: Query | None = None

    def compile_query(self, query: Query) -> _CompiledQuery:
        """Stores the received query and returns a fake compilation."""
        self.last_query = query
        return _CompiledQuery()

    def compile_sort(self, sort: Sort) -> _CompiledQuery:
        """Unused in this test module."""
        del sort
        return _CompiledQuery()

    def compile_page_request(
        self,
        page_request: PageRequest,
    ) -> _CompiledQuery:
        """Unused in this test module."""
        del page_request
        return _CompiledQuery()


def test_parse_returns_query_object() -> None:
    """Ensures the package-level parse helper builds a query object."""
    query = pyrsql.parse("name==demo")
    assert query.text == "name==demo"
    assert query.options.strict_equality is False
    assert query.expression is not None
    assert query.bound_expression is not None


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
    assert query.bound_expression.operator.name == "all_match"


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
    assert query.bound_expression.operator.name == "all_match"


def test_query_options_reject_mismatched_custom_predicate_key() -> None:
    """Rejects custom predicate definitions keyed by the wrong name."""
    with pytest.raises(ValueError, match="(?i)predicate"):
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


def test_compile_uses_orm_and_returns_compilation_result() -> None:
    """Builds a compilation result through the high-level API."""
    orm = _ORM()
    result = pyrsql.compile("name==demo", orm=orm)
    assert isinstance(result, CompilationResult)
    assert result.orm_name == "fake-orm"
    assert orm.last_query is not None
    assert orm.last_query.text == "name==demo"
    assert orm.last_query.bound_expression is not None


def test_apply_compiles_and_applies_query_to_target() -> None:
    """Compiles and applies a query through the high-level API."""
    orm = _ORM()

    class _Model:
        pass

    target = object()
    applied = pyrsql.apply(
        target,
        _Model,
        "name==demo",
        orm=orm,
    )
    assert applied == (target, _Model)
