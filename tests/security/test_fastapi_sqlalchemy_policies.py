"""Security tests for allowlist and denylist enforcement at the API edge."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pyrsql.adapters.fastapi import FastAPICriteriaConfig
from pyrsql.core.options import QueryOptions, SortOptions

if TYPE_CHECKING:
    from collections.abc import Callable

    from fastapi.testclient import TestClient

pytestmark = [
    pytest.mark.security,
    pytest.mark.functional,
    pytest.mark.fastapi,
    pytest.mark.sqlalchemy,
]

QUERY_SEMANTIC_TYPE = "urn:pyrsql:problem:query-semantic-error"
SORT_SEMANTIC_TYPE = "urn:pyrsql:problem:sort-semantic-error"


def test_integration_rejects_filter_field_outside_whitelist(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Rejects filter selectors not present in the configured allowlist."""
    client = integration_app_factory(
        criteria_config=FastAPICriteriaConfig(
            query_options=QueryOptions(field_whitelist=frozenset({"name"})),
        ),
    )

    response = client.get("/users", params={"filter": "company.name==acme"})

    assert response.status_code == 422
    assert response.json()["detail"]["type"] == QUERY_SEMANTIC_TYPE
    assert response.json()["detail"]["errors"][0]["code"] == (
        "field_not_whitelisted"
    )


def test_integration_rejects_filter_field_in_blacklist(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Rejects filter selectors explicitly blocked by configuration."""
    client = integration_app_factory(
        criteria_config=FastAPICriteriaConfig(
            query_options=QueryOptions(field_blacklist=frozenset({"name"})),
        ),
    )

    response = client.get("/users", params={"filter": "name==demo"})

    assert response.status_code == 422
    assert response.json()["detail"]["type"] == QUERY_SEMANTIC_TYPE
    assert response.json()["detail"]["errors"][0]["code"] == (
        "field_blacklisted"
    )


def test_integration_rejects_filter_function_outside_whitelist(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Rejects unapproved functions before any ORM translation happens."""
    client = integration_app_factory(
        criteria_config=FastAPICriteriaConfig(
            query_options=QueryOptions(procedure_whitelist=("lower",)),
        ),
    )

    response = client.get("/users", params={"filter": "@upper[name]==DEMO"})

    assert response.status_code == 422
    assert response.json()["detail"]["type"] == QUERY_SEMANTIC_TYPE
    assert response.json()["detail"]["errors"][0]["code"] == (
        "function_not_whitelisted"
    )


def test_integration_rejects_filter_function_in_blacklist(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Rejects explicitly denied functions even if they match the allowlist."""
    client = integration_app_factory(
        criteria_config=FastAPICriteriaConfig(
            query_options=QueryOptions(
                procedure_whitelist=(".*",),
                procedure_blacklist=("upper",),
            ),
        ),
    )

    response = client.get("/users", params={"filter": "@upper[name]==DEMO"})

    assert response.status_code == 422
    assert response.json()["detail"]["type"] == QUERY_SEMANTIC_TYPE
    assert response.json()["detail"]["errors"][0]["code"] == (
        "function_blacklisted"
    )


def test_integration_rejects_sort_field_outside_whitelist(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Rejects sort selectors not present in the configured allowlist."""
    client = integration_app_factory(
        criteria_config=FastAPICriteriaConfig(
            sort_options=SortOptions(field_whitelist=frozenset({"name"})),
        ),
    )

    response = client.get("/users", params={"sort": "company.name,asc"})

    assert response.status_code == 422
    assert response.json()["detail"]["type"] == SORT_SEMANTIC_TYPE
    assert response.json()["detail"]["errors"][0]["code"] == (
        "sort_field_not_whitelisted"
    )


def test_integration_rejects_sort_field_in_blacklist(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Rejects sort selectors explicitly blocked by configuration."""
    client = integration_app_factory(
        criteria_config=FastAPICriteriaConfig(
            sort_options=SortOptions(field_blacklist=frozenset({"name"})),
        ),
    )

    response = client.get("/users", params={"sort": "name,asc"})

    assert response.status_code == 422
    assert response.json()["detail"]["type"] == SORT_SEMANTIC_TYPE
    assert response.json()["detail"]["errors"][0]["code"] == (
        "sort_field_blacklisted"
    )


def test_integration_rejects_sort_function_outside_whitelist(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Rejects unapproved sort functions before any SQL is generated."""
    client = integration_app_factory(
        criteria_config=FastAPICriteriaConfig(
            sort_options=SortOptions(procedure_whitelist=("lower",)),
        ),
    )

    response = client.get("/users", params={"sort": "@upper[name],asc"})

    assert response.status_code == 422
    assert response.json()["detail"]["type"] == SORT_SEMANTIC_TYPE
    assert response.json()["detail"]["errors"][0]["code"] == (
        "sort_function_not_whitelisted"
    )


def test_integration_rejects_sort_function_in_blacklist(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Rejects explicitly denied sort functions even if globally allowed."""
    client = integration_app_factory(
        criteria_config=FastAPICriteriaConfig(
            sort_options=SortOptions(
                procedure_whitelist=(".*",),
                procedure_blacklist=("upper",),
            ),
        ),
    )

    response = client.get("/users", params={"sort": "@upper[name],asc"})

    assert response.status_code == 422
    assert response.json()["detail"]["type"] == SORT_SEMANTIC_TYPE
    assert response.json()["detail"]["errors"][0]["code"] == (
        "sort_function_blacklisted"
    )
