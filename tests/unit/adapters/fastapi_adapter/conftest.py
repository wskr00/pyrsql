"""Shared fixtures for FastAPI adapter unit tests."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

import pytest

from pyrsql.adapters.fastapi import FastAPICriteriaConfig
from pyrsql.core.options import QueryOptions, SortOptions
from pyrsql.core.page import PageRequest
from pyrsql.core.query import Query
from pyrsql.core.sort import Sort
from pyrsql.ir.query import BoundComparison
from pyrsql.parsing.ast import Expression


@pytest.fixture
def query_stub() -> Query:
    """Provides a minimal Query instance without invoking parsing."""
    query = object.__new__(Query)
    object.__setattr__(query, "text", "stub")
    object.__setattr__(query, "options", QueryOptions())
    object.__setattr__(query, "expression", cast(Expression, object()))
    object.__setattr__(
        query,
        "bound_expression",
        cast(BoundComparison, object()),
    )
    return query


@pytest.fixture
def sort_stub() -> Sort:
    """Provides a minimal Sort instance without invoking parsing."""
    sort = object.__new__(Sort)
    object.__setattr__(sort, "text", "name,asc")
    object.__setattr__(sort, "options", SortOptions())
    object.__setattr__(sort, "fields", ())
    object.__setattr__(sort, "bound_sort", None)
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
        }
    }


@pytest.fixture
def criteria_config(
    openapi_examples: Mapping[str, Any],
) -> FastAPICriteriaConfig:
    """Provides a reusable adapter config with examples."""
    return FastAPICriteriaConfig(filter_openapi_examples=openapi_examples)
