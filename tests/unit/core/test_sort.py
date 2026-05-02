"""Unit tests for the high-level sort object."""

from dataclasses import dataclass
from typing import Any

from pyrsql.backends.base import Backend
from pyrsql.core.sort import Sort


@dataclass(frozen=True, slots=True)
class _FakeCompiledSort:
    result: Any

    def apply(self, target: Any, model: type[Any]) -> Any:
        return {
            "result": self.result,
            "target": target,
            "model": model,
        }


class _FakeBackend(Backend):
    """Minimal backend double for sort unit tests."""

    @property
    def name(self) -> str:
        return "fake"

    def compile_query(self, query: Any) -> Any:
        raise NotImplementedError

    def compile_sort(self, sort: Sort) -> _FakeCompiledSort:
        return _FakeCompiledSort(result=sort.text)

    def compile_page_request(self, page_request: Any) -> Any:
        raise NotImplementedError


def test_sort_parse_builds_sort_object() -> None:
    """Builds a sort object with parsed and semantic fields."""
    sort = Sort.parse("name,desc")
    assert sort.text == "name,desc"
    assert len(sort.fields) == 1
    assert len(sort.semantic_fields) == 1


def test_sort_compile_uses_backend_name() -> None:
    """Compiles the sort with the selected backend metadata."""
    compilation = Sort.parse("name,asc").compile(backend=_FakeBackend())
    assert compilation.backend_name == "fake"


def test_sort_apply_uses_backend() -> None:
    """Compiles and applies the sort using the selected backend."""
    applied = Sort.parse("name,asc").apply(
        target="statement",
        model=str,
        backend=_FakeBackend(),
    )
    assert applied["result"] == "name,asc"
    assert applied["target"] == "statement"
    assert applied["model"] is str
