"""Unit tests for bound logical pagination nodes."""

from __future__ import annotations

import pytest

from pyrsql.ir.page import BoundPage


def test_bound_page_exposes_offset_and_limit() -> None:
    """Computes offset and limit from page number and size."""
    page = BoundPage(page_number=2, page_size=25)

    assert page.offset == 50
    assert page.limit == 25


@pytest.mark.parametrize(
    ("page_number", "page_size", "pattern"),
    [
        pytest.param(-1, 10, r"page_number", id="negative-page-number"),
        pytest.param(0, 0, r"page_size", id="non-positive-page-size"),
    ],
)
def test_bound_page_rejects_invalid_values(
    page_number: int,
    page_size: int,
    pattern: str,
) -> None:
    """Rejects invalid pagination values."""
    with pytest.raises(ValueError, match=pattern):
        BoundPage(page_number=page_number, page_size=page_size)
