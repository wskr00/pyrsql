"""Unit tests for the high-level query object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrsql.core.options import QueryOptions
from pyrsql.core.query import Query

if TYPE_CHECKING:
    from collections.abc import Callable

    import pytest

    from pyrsql.orms.base import ORM


def test_query_parse_builds_query_object_from_parser_and_binder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Composes parsed syntax and bound IR into one Query object."""
    options = QueryOptions(strict_equality=True)
    expression = object()
    bound_expression = object()

    monkeypatch.setattr(
        Query,
        "parse_expression",
        staticmethod(lambda query_text, *, options: expression),
    )
    monkeypatch.setattr(
        Query,
        "bind_expression",
        staticmethod(lambda parsed_expression, *, options: bound_expression),
    )

    query = Query.parse("name==demo", options=options)

    assert query.text == "name==demo"
    assert query.options is options
    assert query.expression is expression
    assert query.bound_expression is bound_expression


def test_query_parse_resolves_shared_default_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Uses the shared immutable default options when none are provided."""
    captured_options: list[QueryOptions] = []
    expression = object()
    bound_expression = object()

    def _parse_expression(query_text: str, *, options: QueryOptions) -> object:
        del query_text
        captured_options.append(options)
        return expression

    def _bind_expression(
        parsed_expression: object,
        *,
        options: QueryOptions,
    ) -> object:
        assert parsed_expression is expression
        captured_options.append(options)
        return bound_expression

    monkeypatch.setattr(
        Query,
        "parse_expression",
        staticmethod(_parse_expression),
    )
    monkeypatch.setattr(
        Query,
        "bind_expression",
        staticmethod(_bind_expression),
    )

    query = Query.parse("name==demo")

    assert query.options is captured_options[0]
    assert captured_options[0] is captured_options[1]


def test_query_compile_uses_orm_name(
    fake_orm_factory: Callable[..., ORM],
) -> None:
    """Compiles the query with the selected ORM metadata."""
    compilation = Query.parse("name==demo").compile(orm=fake_orm_factory())

    assert compilation.orm_name == "fake"


def test_query_apply_uses_orm(
    fake_orm_factory: Callable[..., ORM],
) -> None:
    """Compiles and applies the query using the selected ORM."""
    applied = Query.parse("name==demo").apply(
        target="statement",
        model=str,
        orm=fake_orm_factory(),
    )

    assert applied["result"] == "name==demo"
    assert applied["target"] == "statement"
    assert applied["model"] is str
