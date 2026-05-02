"""Unit tests for the high-level sort object."""

from dataclasses import dataclass
from typing import Any

from pyrsql.orms.base import ORM
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


class _FakeORM(ORM):
    """Minimal ORM double for sort unit tests."""

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


def test_sort_compile_uses_orm_name() -> None:
    """Compiles the sort with the selected ORM metadata."""
    compilation = Sort.parse("name,asc").compile(orm=_FakeORM())
    assert compilation.orm_name == "fake"


def test_sort_apply_uses_orm() -> None:
    """Compiles and applies the sort using the selected orm."""
    applied = Sort.parse("name,asc").apply(
        target="statement",
        model=str,
        orm=_FakeORM(),
    )
    assert applied["result"] == "name,asc"
    assert applied["target"] == "statement"
    assert applied["model"] is str
