"""Unit tests for FastAPI request criteria objects."""

from __future__ import annotations

from typing import Any, cast

import pytest

from pyrsql.adapters.fastapi import (
    CriteriaDependency,
    RequestCriteria,
    criteria_dependency,
)
from pyrsql.core.page import PageRequest
from pyrsql.core.query import Query
from pyrsql.core.sort import Sort
from pyrsql.orms.base import (
    ORM,
    CompiledPageRequest,
    CompiledQuery,
    CompiledSort,
)

pytestmark = [pytest.mark.fastapi]


class _UnusedORM(ORM):
    """Minimal ORM placeholder for isolated RequestCriteria.apply tests."""

    @property
    def name(self) -> str:
        return "unused"

    def compile_query(self, query: Query) -> CompiledQuery:
        del query
        raise AssertionError(
            "compile_query should not be called in this unit test",
        )

    def compile_sort(self, sort: Sort) -> CompiledSort:
        del sort
        raise AssertionError(
            "compile_sort should not be called in this unit test",
        )

    def compile_page_request(
        self,
        page_request: PageRequest,
    ) -> CompiledPageRequest:
        del page_request
        raise AssertionError(
            "compile_page_request should not be called in this unit test",
        )


def test_request_criteria_reports_empty_state(query_stub: Query) -> None:
    """Indicates whether any request criteria were populated."""
    assert RequestCriteria().is_empty is True
    assert RequestCriteria(query=query_stub).is_empty is False


@pytest.mark.parametrize(
    ("kwargs", "pattern"),
    [
        pytest.param({"query": "invalid"}, r"query", id="invalid-query"),
        pytest.param({"sort": "invalid"}, r"sort", id="invalid-sort"),
        pytest.param(
            {"page_request": "invalid"},
            r"page_request",
            id="invalid-page-request",
        ),
    ],
)
def test_request_criteria_rejects_invalid_member_types(
    kwargs: dict[str, object],
    pattern: str,
) -> None:
    """Rejects criteria payloads with invalid runtime types."""
    with pytest.raises(TypeError, match=pattern):
        RequestCriteria(**cast("Any", kwargs))


def test_request_criteria_applies_query_sort_and_page_in_order(
    query_stub: Query,
    sort_stub: Sort,
    page_request: PageRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Applies populated components in query, sort, page order."""
    orm = _UnusedORM()
    criteria = RequestCriteria(
        query=query_stub,
        sort=sort_stub,
        page_request=page_request,
    )
    call_order: list[str] = []

    def fake_query_apply(
        self: Query,
        target: list[str],
        model: type[Any],
        *,
        orm: ORM,
    ) -> list[str]:
        assert self is query_stub
        assert model is object
        assert orm is not None
        target.append("query")
        call_order.append("query")
        return target

    def fake_sort_apply(
        self: Sort,
        target: list[str],
        model: type[Any],
        *,
        orm: ORM,
    ) -> list[str]:
        assert self is sort_stub
        assert model is object
        assert orm is not None
        target.append("sort")
        call_order.append("sort")
        return target

    def fake_page_apply(
        self: PageRequest,
        target: list[str],
        model: type[Any],
        *,
        orm: ORM,
    ) -> list[str]:
        assert self is page_request
        assert model is object
        assert orm is not None
        target.append("page")
        call_order.append("page")
        return target

    monkeypatch.setattr(Query, "apply", fake_query_apply)
    monkeypatch.setattr(Sort, "apply", fake_sort_apply)
    monkeypatch.setattr(PageRequest, "apply", fake_page_apply)

    applied = criteria.apply([], object, orm=orm)

    assert applied == ["query", "sort", "page"]
    assert call_order == ["query", "sort", "page"]


def test_criteria_dependency_exposes_a_fastapi_signature() -> None:
    """Exposes the generated dependency signature for FastAPI inspection."""
    dependency = CriteriaDependency()

    assert "filter_value" in dependency.__signature__.parameters
    assert "sort_value" in dependency.__signature__.parameters


def test_criteria_dependency_factory_reuses_default_dependency() -> None:
    """Reuses the shared dependency instance for the default config."""
    assert criteria_dependency() is criteria_dependency()
