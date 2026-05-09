"""Unit tests for bound logical sort nodes."""

from __future__ import annotations

import pytest

from pyrsql.ir.query import BoundField, BoundFunction
from pyrsql.ir.sort import BoundSort, BoundSortField
from pyrsql.sorting.ast import SortDirection

from .test_query import _bound_field


def test_bound_sort_keeps_fields() -> None:
    """Stores bound sort fields as an immutable tuple."""
    sort = BoundSort(
        fields=(
            BoundSortField(
                selector=_bound_field("companyName", "company.name"),
                direction=SortDirection.DESCENDING,
                ignore_case=False,
            ),
        )
    )

    assert len(sort.fields) == 1
    assert isinstance(sort.fields[0].selector, BoundField)
    assert sort.fields[0].selector.field_path == "company.name"


def test_bound_sort_supports_function_selectors() -> None:
    """Allows sort fields to reference bound function selectors."""
    field = BoundSortField(
        selector=BoundFunction(
            function_name="upper",
            arguments=(_bound_field("companyName", "company.name"),),
        ),
        direction=SortDirection.ASCENDING,
        ignore_case=True,
    )

    assert isinstance(field.selector, BoundFunction)
    assert field.ignore_case is True
    assert field.direction is SortDirection.ASCENDING


@pytest.mark.parametrize(
    ("factory", "pattern"),
    [
        pytest.param(
            lambda: BoundSort(fields=()),
            r"at least one bound sort field",
            id="empty-sort",
        ),
        pytest.param(
            lambda: BoundSortField(
                selector=_bound_field("companyName", "company.name"),
                direction=SortDirection.ASCENDING,
                ignore_case="invalid",  # type: ignore[arg-type]
            ),
            r"ignore_case must be a bool",
            id="invalid-ignore-case",
        ),
    ],
)
def test_bound_sort_nodes_reject_invalid_construction(
    factory: object,
    pattern: str,
) -> None:
    """Rejects invalid bound sort invariants."""
    with pytest.raises((TypeError, ValueError), match=pattern):
        factory()  # type: ignore[operator]
