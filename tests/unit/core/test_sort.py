"""Unit tests for the high-level sort object."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock, sentinel

from pyrsql.core.options import SortOptions
from pyrsql.core.sort import Sort

if TYPE_CHECKING:
    from collections.abc import Callable

    import pytest

    from pyrsql.orms.base import ORM


def test_sort_parse_builds_sort_object_from_parser_and_binder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Composes parsed sort fields and bound sort IR into one Sort object."""
    options = SortOptions()
    parse_fields_mock = Mock(return_value=sentinel.FIELDS)
    bind_fields_mock = Mock(return_value=sentinel.BOUND_SORT)

    monkeypatch.setattr(Sort, "parse_fields", staticmethod(parse_fields_mock))
    monkeypatch.setattr(Sort, "bind_fields", staticmethod(bind_fields_mock))

    sort = Sort.parse("name,desc", options=options)

    assert sort.text == "name,desc"
    assert sort.options is options
    assert sort.fields is sentinel.FIELDS
    assert sort.bound_sort is sentinel.BOUND_SORT
    parse_fields_mock.assert_called_once_with("name,desc", options=options)
    bind_fields_mock.assert_called_once_with(
        sentinel.FIELDS,
        options=options,
    )


def test_sort_parse_keeps_empty_bound_sort_when_no_fields_are_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keeps the bound sort empty when parsing yields no fields."""
    parse_fields_mock = Mock(return_value=())
    bind_fields_mock = Mock(return_value=None)

    monkeypatch.setattr(Sort, "parse_fields", staticmethod(parse_fields_mock))
    monkeypatch.setattr(Sort, "bind_fields", staticmethod(bind_fields_mock))

    sort = Sort.parse(None)

    assert not sort.fields
    assert sort.bound_sort is None
    assert sort.options is not None
    parse_fields_mock.assert_called_once_with(
        None,
        options=sort.options,
    )
    bind_fields_mock.assert_called_once_with(
        (),
        options=sort.options,
    )


def test_sort_compile_returns_orm_artifact(
    fake_orm_factory: Callable[..., ORM],
) -> None:
    """Returns the sort artifact produced by the selected ORM."""
    compilation = Sort.parse("name,asc").compile(orm=fake_orm_factory())

    assert compilation.result == "name,asc"


def test_sort_apply_uses_orm(
    fake_orm_factory: Callable[..., ORM],
) -> None:
    """Compiles and applies the sort using the selected ORM."""
    applied = Sort.parse("name,asc").apply(
        target="statement",
        model=str,
        orm=fake_orm_factory(),
    )

    assert applied["result"] == "name,asc"  # type: ignore[index]
    assert applied["target"] == "statement"  # type: ignore[index]
    assert applied["model"] is str  # type: ignore[index,comparison-overlap]
