"""Unit tests for FastAPI request criteria objects."""

from typing import Any

import pytest

from pyrsql.adapters.fastapi import (
    CriteriaDependency,
    RequestCriteria,
    criteria_dependency,
)
from pyrsql.core.page import PageRequest
from pyrsql.core.query import Query
from pyrsql.core.sort import Sort
from pyrsql.orms.base import ORM

pytestmark = [pytest.mark.unit, pytest.mark.fastapi]


class RecordingCompiled:
    """Records application order for a fake ORM compilation."""

    def __init__(self, name: str, calls: list[str]) -> None:
        self._name = name
        self._calls = calls

    def apply(self, target: list[str], model: type[Any]) -> list[str]:
        """Appends the compilation name to the call sequence."""
        del model
        target.append(self._name)
        self._calls.append(self._name)
        return target


class RecordingORM(ORM):
    """Minimal ORM fake used to test RequestCriteria ordering."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    @property
    def name(self) -> str:
        return "recording"

    def compile_query(self, query: Query) -> RecordingCompiled:
        del query
        return RecordingCompiled("query", self.calls)

    def compile_sort(self, sort: Sort) -> RecordingCompiled:
        del sort
        return RecordingCompiled("sort", self.calls)

    def compile_page_request(
        self,
        page_request: PageRequest,
    ) -> RecordingCompiled:
        del page_request
        return RecordingCompiled("page", self.calls)


def test_request_criteria_reports_empty_state() -> None:
    """Indicates whether any request criteria were populated."""
    assert RequestCriteria().is_empty is True
    assert RequestCriteria(query=Query.parse("name==demo")).is_empty is False


def test_request_criteria_rejects_invalid_member_types() -> None:
    """Rejects criteria payloads with invalid runtime types."""
    with pytest.raises(TypeError, match="(?i)query"):
        RequestCriteria(query="invalid")  # type: ignore[arg-type]


def test_request_criteria_applies_query_sort_and_page_in_order() -> None:
    """Applies populated components in query, sort, page order."""
    orm = RecordingORM()
    criteria = RequestCriteria(
        query=Query.parse("name==demo"),
        sort=Sort.parse("name,asc"),
        page_request=PageRequest.of(0, 10),
    )

    applied = criteria.apply([], object, orm=orm)

    assert applied == ["query", "sort", "page"]
    assert orm.calls == ["query", "sort", "page"]


def test_criteria_dependency_exposes_a_fastapi_signature() -> None:
    """Exposes the generated dependency signature for FastAPI inspection."""
    dependency = CriteriaDependency()

    assert "filter_value" in dependency.__signature__.parameters
    assert "sort_value" in dependency.__signature__.parameters


def test_criteria_dependency_factory_reuses_default_dependency() -> None:
    """Reuses the shared dependency instance for the default config."""
    assert criteria_dependency() is criteria_dependency()
