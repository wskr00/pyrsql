"""Unit tests for bound logical pagination nodes."""

import pytest

from pyrsql.ir.page import BoundPage


def test_bound_page_exposes_offset_and_limit() -> None:
    """Computes offset and limit from page number and size."""
    page = BoundPage(page_number=2, page_size=25)
    assert page.offset == 50
    assert page.limit == 25


def test_bound_page_rejects_negative_page_number() -> None:
    """Rejects invalid negative page numbers."""
    with pytest.raises(ValueError, match="page_number"):
        BoundPage(page_number=-1, page_size=10)


def test_bound_page_rejects_non_positive_page_size() -> None:
    """Rejects invalid non-positive page sizes."""
    with pytest.raises(ValueError, match="page_size"):
        BoundPage(page_number=0, page_size=0)
