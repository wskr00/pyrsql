"""Shared pytest fixtures and test doubles for core unit tests."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

import pytest

from pyrsql.core.page import PageRequest
from pyrsql.core.query import Query
from pyrsql.core.sort import Sort
from pyrsql.orms.base import ORM


@dataclass(frozen=True, slots=True)
class FakeCompiledResult:
    """Minimal compiled object used by core unit tests."""

    result: object

    def apply(self, target: object, model: type[object]) -> dict[str, object]:
        """Returns the received target and model together with a payload."""
        return {
            "result": self.result,
            "target": target,
            "model": model,
        }


class FakeORM(ORM):
    """Configurable ORM double for core unit tests."""

    __slots__ = ("query_result", "sort_result", "page_result")

    def __init__(
        self,
        *,
        query_result: object | None = None,
        sort_result: object | None = None,
        page_result: object | None = None,
    ) -> None:
        self.query_result = query_result
        self.sort_result = sort_result
        self.page_result = page_result

    @property
    def name(self) -> str:
        """Returns a stable fake ORM name."""
        return "fake"

    def compile_query(self, query: Query) -> FakeCompiledResult:
        """Builds a fake compiled query result."""
        result = (
            self.query_result
            if self.query_result is not None
            else query.text
        )
        return FakeCompiledResult(result=result)

    def compile_sort(self, sort: Sort) -> FakeCompiledResult:
        """Builds a fake compiled sort result."""
        result = self.sort_result if self.sort_result is not None else sort.text
        return FakeCompiledResult(result=result)

    def compile_page_request(
        self,
        page_request: PageRequest,
    ) -> FakeCompiledResult:
        """Builds a fake compiled page result."""
        result = (
            self.page_result
            if self.page_result is not None
            else page_request.page_number
        )
        return FakeCompiledResult(result=result)


@pytest.fixture
def fake_orm_factory() -> Callable[..., FakeORM]:
    """Provides a typed fake ORM factory for core unit tests."""

    def factory(
        *,
        query_result: object | None = None,
        sort_result: object | None = None,
        page_result: object | None = None,
    ) -> FakeORM:
        return FakeORM(
            query_result=query_result,
            sort_result=sort_result,
            page_result=page_result,
        )

    return factory
