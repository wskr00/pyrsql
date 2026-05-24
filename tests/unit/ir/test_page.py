"""Unit tests for bound logical pagination nodes."""

from __future__ import annotations

from pyrsql.ir.page import BoundPage


def test_bound_page_exposes_offset_and_limit() -> None:
    """Computes offset and limit from page number and size."""
    page = BoundPage(page_number=2, page_size=25)

    assert page.offset == 50
    assert page.limit == 25
