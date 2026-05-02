"""Unit tests for backend-neutral pagination objects."""

from dataclasses import dataclass
from typing import Any

import pytest

from pyrsql.backends.base import Backend
from pyrsql.core.page import PageRequest


@dataclass(frozen=True, slots=True)
class _FakeCompiledPageRequest:
    result: Any

    def apply(self, target: Any, model: type[Any]) -> Any:
        return {
            "result": self.result,
            "target": target,
            "model": model,
        }


class _FakeBackend(Backend):
    """Minimal backend double for page-request unit tests."""

    @property
    def name(self) -> str:
        return "fake"

    def compile_query(self, query: Any) -> Any:
        raise NotImplementedError

    def compile_sort(self, sort: Any) -> Any:
        raise NotImplementedError

    def compile_page_request(
        self,
        page_request: PageRequest,
    ) -> _FakeCompiledPageRequest:
        return _FakeCompiledPageRequest(result=page_request.page_number)


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
    compilation = PageRequest.of(0, 10).compile(backend=_FakeBackend())
    assert compilation.backend_name == "fake"


def test_page_request_apply_uses_backend() -> None:
    """Compiles and applies a page request through the selected backend."""
    applied = PageRequest.of(0, 10).apply(
        target="statement",
        model=str,
        backend=_FakeBackend(),
    )
    assert applied["result"] == 0
    assert applied["target"] == "statement"
    assert applied["model"] is str
