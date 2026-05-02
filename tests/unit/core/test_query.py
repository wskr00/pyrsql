"""Unit tests for the high-level query object."""

from dataclasses import dataclass
from typing import Any

from pyrsql.orms.base import ORM
from pyrsql.core.options import QueryOptions
from pyrsql.core.query import Query
from pyrsql.parsing.operators import ComparisonOperator
from pyrsql.parsing.operators import DEFAULT_OPERATOR_REGISTRY
from pyrsql.parsing.operators import OperatorRegistry


@dataclass(frozen=True, slots=True)
class _FakeCompiledQuery:
    result: Any

    def apply(self, target: Any, model: type[Any]) -> Any:
        return {
            "result": self.result,
            "target": target,
            "model": model,
        }


class _FakeORM(ORM):
    """Minimal ORM double for query unit tests."""

    @property
    def name(self) -> str:
        return "fake"

    def compile_query(self, query: Query) -> _FakeCompiledQuery:
        return _FakeCompiledQuery(result=query.text)

    def compile_sort(self, sort: Any) -> Any:
        raise NotImplementedError

    def compile_page_request(self, page_request: Any) -> Any:
        raise NotImplementedError


def test_query_parse_builds_query_object() -> None:
    """Builds a query with parsed and semantic expressions."""
    query = Query.parse("name==demo")
    assert query.text == "name==demo"
    assert query.options.strict_equality is False
    assert query.expression is not None
    assert query.semantic_expression is not None


def test_query_parse_uses_custom_operator_registry() -> None:
    """Honors custom operator configuration while parsing."""
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
    query = Query.parse("name=all=demo", options=options)
    assert query.expression is not None
    assert query.expression.operator.name == "all_match"


def test_query_compile_uses_orm_name() -> None:
    """Compiles the query with the selected ORM metadata."""
    compilation = Query.parse("name==demo").compile(orm=_FakeORM())
    assert compilation.orm_name == "fake"


def test_query_apply_uses_orm() -> None:
    """Compiles and applies the query using the selected orm."""
    applied = Query.parse("name==demo").apply(
        target="statement",
        model=str,
        orm=_FakeORM(),
    )
    assert applied["result"] == "name==demo"
    assert applied["target"] == "statement"
    assert applied["model"] is str
