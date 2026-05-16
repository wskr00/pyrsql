"""Shared fixtures and helpers for security-focused tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

pytest.importorskip("fastapi")
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from tests.functional.fastapi_sqlalchemy.conftest import User

from pyrsql.integrations.fastapi import FastAPISQLAlchemyIntegration

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyrsql.adapters.fastapi import FastAPICriteriaConfig


@pytest.fixture
def integration_app_factory() -> Callable[..., TestClient]:
    """Builds lightweight FastAPI apps for security validation."""

    def build_client(
        *,
        criteria_config: FastAPICriteriaConfig | None = None,
    ) -> TestClient:
        app = FastAPI()
        integration = FastAPISQLAlchemyIntegration(
            criteria_config=criteria_config,
        )

        @app.get("/users")
        def list_users(
            statement: Any = Depends(  # noqa: FAST002
                integration.select_dependency(User),
            ),
        ) -> dict[str, str]:
            return {"sql": str(statement.compile())}

        return TestClient(app, raise_server_exceptions=False)

    return build_client


@pytest.fixture
def compiled_params_app_factory() -> Callable[..., TestClient]:
    """Builds apps that expose compiled SQL params for deterministic checks."""

    def build_client(
        *,
        criteria_config: FastAPICriteriaConfig | None = None,
    ) -> TestClient:
        app = FastAPI()
        integration = FastAPISQLAlchemyIntegration(
            criteria_config=criteria_config,
        )

        @app.get("/users")
        def list_users(
            statement: Any = Depends(  # noqa: FAST002
                integration.select_dependency(User),
            ),
        ) -> dict[str, object]:
            compiled = statement.compile()
            return {"params": compiled.params}

        return TestClient(app, raise_server_exceptions=False)

    return build_client


@pytest.fixture
def resource_app_factory() -> Callable[..., TestClient]:
    """Builds apps backed by declarative FastAPI SQLAlchemy resources."""

    def build_client(
        *,
        filterable_fields: set[str] | frozenset[str] | None = None,
        sortable_fields: set[str] | frozenset[str] | None = None,
    ) -> TestClient:
        app = FastAPI()
        integration = FastAPISQLAlchemyIntegration()
        resource = integration.resource(
            User,
            filterable_fields=filterable_fields,
            sortable_fields=sortable_fields,
        )

        @app.get("/users")
        def list_users(
            statement: Any = Depends(  # noqa: FAST002
                resource.select_dependency(),
            ),
        ) -> dict[str, str]:
            return {"sql": str(statement.compile())}

        return TestClient(app, raise_server_exceptions=False)

    return build_client


def assert_response_hides_internal_error_details(response: Any) -> None:
    """Asserts that one HTTP response does not leak internal error details."""
    assert "Traceback" not in response.text
    assert "sqlalchemy." not in response.text
    assert "/home/lucas/" not in response.text
