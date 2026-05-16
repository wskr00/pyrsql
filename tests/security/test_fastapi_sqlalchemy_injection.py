"""Security tests for FastAPI + SQLAlchemy integration resistance."""

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


def test_integration_returns_http_422_for_malicious_sort_field(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Translates malicious backend sort resolution failures into HTTP 422."""
    response = integration_app_factory().get(
        "/users",
        params={"sort": "name,asc;DROP TABLE users"},
    )

    assert response.status_code == 422
    assert '"parameter":"sort"' in response.text
    assert '"type":"sort_backend_error"' in response.text
    assert '"field":"DROP TABLE users"' in response.text


def test_integration_returns_http_422_for_malicious_filter_field(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Translates backend field resolution failures into HTTP 422."""
    response = integration_app_factory().get(
        "/users",
        params={"filter": "password==demo"},
    )

    assert response.status_code == 422
    assert '"parameter":"filter"' in response.text
    assert '"type":"query_backend_error"' in response.text
    assert '"field":"password"' in response.text
