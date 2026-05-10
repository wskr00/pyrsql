"""Shared fixtures for FastAPI adapter unit tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import pytest

from pyrsql.adapters.fastapi import FastAPICriteriaConfig
from pyrsql.core.options import QueryOptions, SortOptions
from pyrsql.core.page import PageRequest
from pyrsql.core.query import Query
from pyrsql.core.sort import Sort

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pyrsql.ir.query import BoundComparison
    from pyrsql.parsing.ast import Expression


@pytest.fixture
def query_stub() -> Query:
    """Provides a minimal Query instance without invoking parsing."""
    query = object.__new__(Query)
    object.__setattr__(query, "text", "stub")  # noqa: PLC2801
    object.__setattr__(query, "options", QueryOptions())  # noqa: PLC2801
    object.__setattr__(query, "expression", cast("Expression", object()))  # noqa: PLC2801
    object.__setattr__(  # noqa: PLC2801
        query,
        "bound_expression",
        cast("BoundComparison", object()),
    )
    return query


@pytest.fixture
def sort_stub() -> Sort:
    """Provides a minimal Sort instance without invoking parsing."""
    sort = object.__new__(Sort)
    object.__setattr__(sort, "text", "name,asc")  # noqa: PLC2801
    object.__setattr__(sort, "options", SortOptions())  # noqa: PLC2801
    object.__setattr__(sort, "fields", ())  # noqa: PLC2801
    object.__setattr__(sort, "bound_sort", None)  # noqa: PLC2801
    return sort


@pytest.fixture
def page_request() -> PageRequest:
    """Provides a simple validated page request."""
    return PageRequest.of(0, 10)


@pytest.fixture(name="openapi_examples")
def openapi_examples_fixture() -> Mapping[str, Any]:
    """Provides reusable OpenAPI examples for adapter config tests."""
    return {
        "by_name": {
            "summary": "By name",
            "value": "name==demo",
        },
    }


@pytest.fixture
def criteria_config(
    openapi_examples: Mapping[str, Any],
) -> FastAPICriteriaConfig:
    """Provides a reusable adapter config with examples."""
    return FastAPICriteriaConfig(filter_openapi_examples=openapi_examples)
