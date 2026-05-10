"""Unit tests for the high-level query object."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock, sentinel

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
    parse_expression_mock = Mock(return_value=sentinel.EXPRESSION)
    bind_expression_mock = Mock(return_value=sentinel.BOUND_EXPRESSION)

    monkeypatch.setattr(
        Query, "parse_expression", staticmethod(parse_expression_mock),
    )
    monkeypatch.setattr(
        Query, "bind_expression", staticmethod(bind_expression_mock),
    )

    query = Query.parse("name==demo", options=options)

    assert query.text == "name==demo"
    assert query.options is options
    assert query.expression is sentinel.EXPRESSION
    assert query.bound_expression is sentinel.BOUND_EXPRESSION
    parse_expression_mock.assert_called_once_with("name==demo", options=options)
    bind_expression_mock.assert_called_once_with(
        sentinel.EXPRESSION, options=options,
    )


def test_query_parse_resolves_shared_default_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Uses the shared immutable default options when none are provided."""
    parse_expression_mock = Mock(return_value=sentinel.EXPRESSION)
    bind_expression_mock = Mock(return_value=sentinel.BOUND_EXPRESSION)

    monkeypatch.setattr(
        Query, "parse_expression", staticmethod(parse_expression_mock),
    )
    monkeypatch.setattr(
        Query, "bind_expression", staticmethod(bind_expression_mock),
    )

    query = Query.parse("name==demo")

    assert query.options is not None
    parse_expression_mock.assert_called_once_with(
        "name==demo", options=query.options,
    )
    bind_expression_mock.assert_called_once_with(
        sentinel.EXPRESSION, options=query.options,
    )


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

    assert applied["result"] == "name==demo"  # type: ignore[index]
    assert applied["target"] == "statement"  # type: ignore[index]
    assert applied["model"] is str  # type: ignore[index,comparison-overlap]
