"""Unit tests for FastAPI request criteria objects."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from unittest.mock import Mock

import pytest
from typing_extensions import override

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
)

if TYPE_CHECKING:
    from pyrsql.orms.base import (
        CompiledPageRequest,
        CompiledQuery,
        CompiledSort,
    )

pytestmark = [pytest.mark.fastapi]


class _UnusedORM(ORM):
    """Minimal ORM placeholder for isolated RequestCriteria.apply tests."""

    @property
    @override
    def name(self) -> str:
        return "unused"

    @override
    def compile_query(self, query: Query) -> CompiledQuery:
        del query
        raise AssertionError(
            "compile_query should not be called in this unit test",
        )

    @override
    def compile_sort(self, sort: Sort) -> CompiledSort:
        del sort
        raise AssertionError(
            "compile_sort should not be called in this unit test",
        )

    @override
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

    fake_query = Mock(
        side_effect=lambda target, model, *, orm: [*target, "query"],
    )
    fake_sort = Mock(
        side_effect=lambda target, model, *, orm: [*target, "sort"],
    )
    fake_page = Mock(
        side_effect=lambda target, model, *, orm: [*target, "page"],
    )

    monkeypatch.setattr(Query, "apply", staticmethod(fake_query))
    monkeypatch.setattr(Sort, "apply", staticmethod(fake_sort))
    monkeypatch.setattr(PageRequest, "apply", staticmethod(fake_page))

    applied: list[object] = criteria.apply([], object, orm=orm)

    assert applied == ["query", "sort", "page"]
    fake_query.assert_called_once_with([], object, orm=orm)
    fake_sort.assert_called_once_with(["query"], object, orm=orm)
    fake_page.assert_called_once_with(
        ["query", "sort"],
        object,
        orm=orm,
    )


def test_criteria_dependency_exposes_a_fastapi_signature() -> None:
    """Exposes the generated dependency signature for FastAPI inspection."""
    dependency = CriteriaDependency()

    assert "filter_value" in dependency.__signature__.parameters
    assert "sort_value" in dependency.__signature__.parameters


def test_criteria_dependency_factory_reuses_default_dependency() -> None:
    """Reuses the shared dependency instance for the default config."""
    assert criteria_dependency() is criteria_dependency()
