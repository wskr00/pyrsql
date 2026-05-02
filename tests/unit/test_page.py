"""Unit tests for backend-neutral pagination objects."""

import pytest

from pyrsql.backends.sqlalchemy import SQLAlchemyBackend
from pyrsql.core.page import PageRequest


def test_page_request_of_builds_offset_and_limit() -> None:
    """Builds a page request from page number and page size."""
    page_request = PageRequest.of(2, 25)
    assert page_request.page_number == 2
    assert page_request.page_size == 25
    assert page_request.offset == 50
    assert page_request.limit == 25


def test_page_request_from_offset_builds_page_request() -> None:
    """Builds a page request from aligned offset and limit values."""
    page_request = PageRequest.from_offset(offset=20, limit=10)
    assert page_request.page_number == 2
    assert page_request.page_size == 10


def test_page_request_rejects_negative_page_number() -> None:
    """Rejects negative page numbers."""
    with pytest.raises(ValueError):
        PageRequest.of(-1, 10)


def test_page_request_rejects_non_positive_page_size() -> None:
    """Rejects non-positive page sizes."""
    with pytest.raises(ValueError):
        PageRequest.of(0, 0)


def test_page_request_rejects_non_aligned_offset() -> None:
    """Rejects offsets that cannot map cleanly to page number and size."""
    with pytest.raises(ValueError):
        PageRequest.from_offset(offset=15, limit=10)


def test_page_request_compile_uses_backend_name() -> None:
    """Ensures page compilation returns the selected backend metadata."""
    compilation = PageRequest.of(0, 10).compile(backend=SQLAlchemyBackend())
    assert compilation.backend_name == "sqlalchemy"
