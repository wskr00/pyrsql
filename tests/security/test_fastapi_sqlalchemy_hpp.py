"""Security tests for duplicate-parameter handling at the API edge."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pyrsql.adapters.fastapi import FastAPICriteriaConfig

if TYPE_CHECKING:
    from collections.abc import Callable

    from fastapi.testclient import TestClient

pytestmark = [
    pytest.mark.security,
    pytest.mark.functional,
    pytest.mark.fastapi,
    pytest.mark.sqlalchemy,
]

QUERY_BACKEND_TYPE = "urn:pyrsql:problem:query-backend-error"
SORT_BACKEND_TYPE = "urn:pyrsql:problem:sort-backend-error"


def test_duplicate_filter_parameters_use_last_value_and_still_validate(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Applies one stable duplicate-parameter rule instead of concatenation."""
    response = integration_app_factory().get(
        "/users",
        params=[("filter", "name==demo"), ("filter", "password==x")],
    )

    assert response.status_code == 422
    assert response.json()["detail"]["type"] == QUERY_BACKEND_TYPE
    assert response.json()["detail"]["errors"][0]["field"] == "password"


def test_duplicate_sort_parameters_use_last_value_and_still_validate(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Rejects a malicious last sort value instead of merging both clauses."""
    response = integration_app_factory().get(
        "/users",
        params=[("sort", "name,asc"), ("sort", "DROP TABLE users")],
    )

    assert response.status_code == 422
    assert response.json()["detail"]["type"] == SORT_BACKEND_TYPE
    assert response.json()["detail"]["errors"][0]["field"] == (
        "DROP TABLE users"
    )


def test_duplicate_page_parameters_use_last_value_consistently(
    compiled_params_app_factory: Callable[..., TestClient],
) -> None:
    """Uses a deterministic last-value rule for duplicate page params."""
    client = compiled_params_app_factory(
        criteria_config=FastAPICriteriaConfig(max_page_size=5),
    )

    response = client.get(
        "/users",
        params=[("page", "1"), ("page", "999"), ("size", "2")],
    )

    assert response.status_code == 200
    assert response.json()["params"]["param_2"] == 1998


def test_duplicate_size_parameters_keep_max_page_size_validation(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Still enforces page-size bounds when the last duplicate is unsafe."""
    response = integration_app_factory(
        criteria_config=FastAPICriteriaConfig(max_page_size=5),
    ).get(
        "/users",
        params=[("size", "1"), ("size", "100000")],
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "size"]
