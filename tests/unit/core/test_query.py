"""Unit tests for the high-level query object."""

from dataclasses import dataclass
from typing import Any

from pyrsql.backends.base import Backend
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


class _FakeBackend(Backend):
    """Minimal backend double for query unit tests."""

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


def test_query_compile_uses_backend_name() -> None:
    """Compiles the query with the selected backend metadata."""
    compilation = Query.parse("name==demo").compile(backend=_FakeBackend())
    assert compilation.backend_name == "fake"


def test_query_apply_uses_backend() -> None:
    """Compiles and applies the query using the selected backend."""
    applied = Query.parse("name==demo").apply(
        target="statement",
        model=str,
        backend=_FakeBackend(),
    )
    assert applied["result"] == "name==demo"
    assert applied["target"] == "statement"
    assert applied["model"] is str
