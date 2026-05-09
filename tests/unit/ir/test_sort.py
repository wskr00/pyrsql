"""Unit tests for bound logical sort nodes."""

import pytest

from pyrsql.ir.query import BoundField, BoundFunction
from pyrsql.ir.sort import BoundSort, BoundSortField
from pyrsql.sorting.ast import SortDirection


def test_bound_sort_keeps_fields() -> None:
    """Stores bound sort fields as an immutable tuple."""
    sort = BoundSort(
        fields=(
            BoundSortField(
                selector=BoundField(
                    raw_path="companyName",
                    field_path="company.name",
                    segments=("company", "name"),
                ),
                direction=SortDirection.DESCENDING,
                ignore_case=False,
            ),
        )
    )
    assert len(sort.fields) == 1
    assert isinstance(sort.fields[0].selector, BoundField)


def test_bound_sort_supports_function_selectors() -> None:
    """Allows sort fields to reference bound function selectors."""
    field = BoundSortField(
        selector=BoundFunction(
            function_name="upper",
            arguments=(
                BoundField(
                    raw_path="companyName",
                    field_path="company.name",
                    segments=("company", "name"),
                ),
            ),
        ),
        direction=SortDirection.ASCENDING,
        ignore_case=True,
    )
    assert isinstance(field.selector, BoundFunction)
    assert isinstance(field.selector.arguments[0], BoundField)


def test_bound_sort_rejects_empty_field_list() -> None:
    """Prevents invalid empty bound sort requests."""
    with pytest.raises(
        ValueError,
        match="at least one bound sort field",
    ):
        BoundSort(fields=())
