"""Unit tests for sorting AST models."""

from __future__ import annotations

from pyrsql.selector.ast import FieldSelector
from pyrsql.sorting.ast import SortDirection, SortField


def test_sort_direction_from_raw_matches_supported_values() -> None:
    """Sort directions normalize supported raw tokens."""
    assert SortDirection.from_raw("asc") is SortDirection.ASCENDING
    assert SortDirection.from_raw("desc") is SortDirection.DESCENDING


def test_sort_field_retains_constructor_values() -> None:
    """Sort fields retain the parsed sort metadata."""
    selector = FieldSelector(raw_path="name", segments=("name",))
    field = SortField(
        selector=selector,
        direction=SortDirection.ASCENDING,
        ignore_case=False,
    )

    assert field.selector is selector
    assert field.direction is SortDirection.ASCENDING
    assert field.ignore_case is False
