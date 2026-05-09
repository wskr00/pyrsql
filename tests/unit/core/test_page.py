"""Unit tests for orm-neutral pagination objects."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pyrsql.core.page import PageRequest

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyrsql.orms.base import ORM


def test_page_request_of_builds_offset_and_limit() -> None:
    """Builds a page request from page number and page size."""
    page_request = PageRequest.of(2, 25)

    assert page_request.page_number == 2
    assert page_request.page_size == 25
    assert page_request.offset == 50
    assert page_request.limit == 25
    assert page_request.bound_page.offset == 50
    assert page_request.bound_page.limit == 25


def test_page_request_from_offset_builds_page_request() -> None:
    """Builds a page request from aligned offset and limit values."""
    page_request = PageRequest.from_offset(offset=20, limit=10)

    assert page_request.page_number == 2
    assert page_request.page_size == 10


@pytest.mark.parametrize(
    ("page_number", "page_size", "pattern"),
    [
        pytest.param(
            -1,
            10,
            "(?i)page[_ ]?number|negative|greater",
            id="negative-page-number",
        ),
        pytest.param(
            0,
            0,
            "(?i)page[_ ]?size|positive|greater",
            id="non-positive-page-size",
        ),
    ],
)
def test_page_request_of_rejects_invalid_inputs(
    page_number: int,
    page_size: int,
    pattern: str,
) -> None:
    """Rejects invalid page number and page size combinations."""
    with pytest.raises(ValueError, match=pattern):
        PageRequest.of(page_number, page_size)


def test_page_request_rejects_non_aligned_offset() -> None:
    """Rejects offsets that cannot map cleanly to page number and size."""
    with pytest.raises(ValueError, match="(?i)offset"):
        PageRequest.from_offset(offset=15, limit=10)


def test_page_request_compile_uses_orm_name(
    fake_orm_factory: Callable[..., ORM],
) -> None:
    """Ensures page compilation returns the selected ORM metadata."""
    compilation = PageRequest.of(0, 10).compile(orm=fake_orm_factory())

    assert compilation.orm_name == "fake"


def test_page_request_apply_uses_orm(
    fake_orm_factory: Callable[..., ORM],
) -> None:
    """Compiles and applies a page request through the selected ORM."""
    applied = PageRequest.of(0, 10).apply(
        target="statement",
        model=str,
        orm=fake_orm_factory(),
    )

    assert applied["result"] == 0
    assert applied["target"] == "statement"
    assert applied["model"] is str
