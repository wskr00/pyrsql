"""Unit tests for the high-level sort object."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from pyrsql.core.options import SortOptions
from pyrsql.core.sort import Sort

if TYPE_CHECKING:
    from collections.abc import Callable

    import pytest

    from pyrsql.orms.base import ORM
    from pyrsql.sorting.ast import SortField


def test_sort_parse_builds_sort_object_from_parser_and_binder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Composes parsed sort fields and bound sort IR into one Sort object."""
    options = SortOptions()
    fields = cast(
        "tuple[SortField, ...]",
        (object(), object()),
    )
    bound_sort = object()

    monkeypatch.setattr(
        Sort,
        "parse_fields",
        staticmethod(lambda sort_text, *, options: fields),
    )
    monkeypatch.setattr(
        Sort,
        "bind_fields",
        staticmethod(lambda parsed_fields, *, options: bound_sort),
    )

    sort = Sort.parse("name,desc", options=options)

    assert sort.text == "name,desc"
    assert sort.options is options
    assert sort.fields is fields
    assert sort.bound_sort is bound_sort


def test_sort_parse_keeps_empty_bound_sort_when_no_fields_are_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keeps the bound sort empty when parsing yields no fields."""
    captured_options: list[SortOptions] = []

    def _parse_fields(
        sort_text: str | None,
        *,
        options: SortOptions,
    ) -> tuple[object, ...]:
        del sort_text
        captured_options.append(options)
        return ()

    def _bind_fields(
        fields: tuple[object, ...],
        *,
        options: SortOptions,
    ) -> object | None:
        assert fields == ()
        captured_options.append(options)
        return None

    monkeypatch.setattr(
        Sort,
        "parse_fields",
        staticmethod(_parse_fields),
    )
    monkeypatch.setattr(
        Sort,
        "bind_fields",
        staticmethod(_bind_fields),
    )

    sort = Sort.parse(None)

    assert not sort.fields
    assert sort.bound_sort is None
    assert sort.options is captured_options[0]
    assert captured_options[0] is captured_options[1]


def test_sort_compile_uses_orm_name(
    fake_orm_factory: Callable[..., ORM],
) -> None:
    """Compiles the sort with the selected ORM metadata."""
    compilation = Sort.parse("name,asc").compile(orm=fake_orm_factory())

    assert compilation.orm_name == "fake"


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
