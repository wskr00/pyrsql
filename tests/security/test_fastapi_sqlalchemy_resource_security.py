"""Security tests for declarative FastAPI SQLAlchemy resources."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

    from fastapi.testclient import TestClient

pytestmark = [
    pytest.mark.security,
    pytest.mark.functional,
    pytest.mark.fastapi,
    pytest.mark.sqlalchemy,
]


def test_resource_rejects_filter_field_outside_declared_allowlist(
    resource_app_factory: Callable[..., TestClient],
) -> None:
    """Rejects filters on fields excluded by declarative resource config."""
    response = resource_app_factory(filterable_fields={"name"}).get(
        "/users",
        params={"filter": "company.name==acme"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["type"] == "query_semantic_error"
    assert response.json()["detail"]["errors"][0]["code"] == (
        "field_not_whitelisted"
    )


def test_resource_rejects_sort_field_outside_declared_allowlist(
    resource_app_factory: Callable[..., TestClient],
) -> None:
    """Rejects sort fields excluded by declarative resource config."""
    response = resource_app_factory(sortable_fields={"name"}).get(
        "/users",
        params={"sort": "company.name,asc"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["type"] == "sort_semantic_error"
    assert response.json()["detail"]["errors"][0]["code"] == (
        "sort_field_not_whitelisted"
    )
