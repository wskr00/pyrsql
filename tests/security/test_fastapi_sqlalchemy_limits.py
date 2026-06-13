"""Security tests for parser and paging limits at the FastAPI boundary."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pyrsql.adapters.fastapi import FastAPICriteriaConfig
from pyrsql.core.options import QueryOptions, SortOptions
from pyrsql.parsing.limits import ParseLimits
from pyrsql.sorting.limits import SortLimits

if TYPE_CHECKING:
    from collections.abc import Callable

    from fastapi.testclient import TestClient

pytestmark = [
    pytest.mark.security,
    pytest.mark.functional,
    pytest.mark.fastapi,
    pytest.mark.sqlalchemy,
]

QUERY_PARSE_TYPE = "urn:pyrsql:problem:query-parse-error"
SORT_PARSE_TYPE = "urn:pyrsql:problem:sort-parse-error"


def test_integration_rejects_filter_exceeding_query_length_limit(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Rejects oversized filter input before it reaches ORM translation."""
    client = integration_app_factory(
        criteria_config=FastAPICriteriaConfig(
            query_options=QueryOptions(
                parse_limits=ParseLimits(max_query_length=9),
            ),
        ),
    )

    response = client.get("/users", params={"filter": "name=='demo'"})

    assert response.status_code == 400
    assert response.json()["detail"]["type"] == QUERY_PARSE_TYPE
    assert response.json()["detail"]["errors"][0]["code"] == "lex_error"


def test_integration_rejects_filter_exceeding_selector_length_limit(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Rejects selectors that exceed the configured maximum field length."""
    client = integration_app_factory(
        criteria_config=FastAPICriteriaConfig(
            query_options=QueryOptions(
                parse_limits=ParseLimits(max_selector_length=4),
            ),
        ),
    )

    response = client.get("/users", params={"filter": "company.name==demo"})

    assert response.status_code == 400
    assert response.json()["detail"]["type"] == QUERY_PARSE_TYPE
    assert response.json()["detail"]["errors"][0]["code"] == "lex_error"


def test_integration_rejects_filter_exceeding_argument_length_limit(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Rejects one argument whose raw text exceeds the configured limit."""
    client = integration_app_factory(
        criteria_config=FastAPICriteriaConfig(
            query_options=QueryOptions(
                parse_limits=ParseLimits(max_argument_length=3),
            ),
        ),
    )

    response = client.get("/users", params={"filter": "name=='demo'"})

    assert response.status_code == 400
    assert response.json()["detail"]["type"] == QUERY_PARSE_TYPE
    assert response.json()["detail"]["errors"][0]["code"] == "lex_error"


def test_integration_rejects_filter_with_too_many_list_arguments(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Rejects list filters that exceed the configured item count."""
    client = integration_app_factory(
        criteria_config=FastAPICriteriaConfig(
            query_options=QueryOptions(
                parse_limits=ParseLimits(max_arguments_per_list=2),
            ),
        ),
    )

    response = client.get("/users", params={"filter": "id=in=(1,2,3)"})

    assert response.status_code == 400
    assert response.json()["detail"]["type"] == QUERY_PARSE_TYPE
    assert response.json()["detail"]["errors"][0]["code"] == "parse_error"


def test_integration_rejects_filter_exceeding_expression_depth_limit(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Rejects deeply nested filter expressions that exceed depth limits."""
    client = integration_app_factory(
        criteria_config=FastAPICriteriaConfig(
            query_options=QueryOptions(
                parse_limits=ParseLimits(max_expression_depth=2),
            ),
        ),
    )

    response = client.get("/users", params={"filter": "((name==demo))"})

    assert response.status_code == 400
    assert response.json()["detail"]["type"] == QUERY_PARSE_TYPE
    assert response.json()["detail"]["errors"][0]["code"] == "parse_error"


def test_integration_rejects_filter_exceeding_node_count_limit(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Rejects filters that exceed the configured AST node budget."""
    client = integration_app_factory(
        criteria_config=FastAPICriteriaConfig(
            query_options=QueryOptions(
                parse_limits=ParseLimits(max_node_count=2),
            ),
        ),
    )

    response = client.get(
        "/users",
        params={"filter": "name==demo;company.name==acme"},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["type"] == QUERY_PARSE_TYPE
    assert response.json()["detail"]["errors"][0]["code"] == "parse_error"


def test_integration_rejects_sort_exceeding_total_length_limit(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Rejects oversized sort clauses before they reach ORM resolution."""
    client = integration_app_factory(
        criteria_config=FastAPICriteriaConfig(
            sort_options=SortOptions(
                sort_limits=SortLimits(max_sort_length=5),
            ),
        ),
    )

    response = client.get("/users", params={"sort": "company.name,desc"})

    assert response.status_code == 400
    assert response.json()["detail"]["type"] == SORT_PARSE_TYPE
    assert response.json()["detail"]["errors"][0]["code"] == "sort_parse_error"


def test_integration_rejects_sort_with_too_many_fields(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Rejects sort clauses that exceed the configured field count limit."""
    client = integration_app_factory(
        criteria_config=FastAPICriteriaConfig(
            sort_options=SortOptions(
                sort_limits=SortLimits(max_fields=1),
            ),
        ),
    )

    response = client.get("/users", params={"sort": "name;company.name"})

    assert response.status_code == 400
    assert response.json()["detail"]["type"] == SORT_PARSE_TYPE
    assert response.json()["detail"]["errors"][0]["code"] == "sort_parse_error"


def test_integration_rejects_sort_exceeding_field_path_length_limit(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Rejects one sort field whose selector exceeds the configured limit."""
    client = integration_app_factory(
        criteria_config=FastAPICriteriaConfig(
            sort_options=SortOptions(
                sort_limits=SortLimits(max_field_path_length=4),
            ),
        ),
    )

    response = client.get("/users", params={"sort": "company.name,asc"})

    assert response.status_code == 400
    assert response.json()["detail"]["type"] == SORT_PARSE_TYPE
    assert response.json()["detail"]["errors"][0]["code"] == "sort_parse_error"


def test_integration_rejects_page_size_above_maximum_limit(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Relies on FastAPI query validation to reject oversized page sizes."""
    client = integration_app_factory(
        criteria_config=FastAPICriteriaConfig(max_page_size=5),
    )

    response = client.get("/users", params={"size": 6})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "size"]
