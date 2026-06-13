"""Async functional tests for the FastAPI criteria dependency."""

from typing import Annotated, Any

import pytest

pytest.importorskip("fastapi")
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from pyrsql.adapters.fastapi import (
    FastAPICriteriaConfig,
    RequestCriteria,
    criteria_dependency,
)
from pyrsql.core.options import QueryOptions

pytestmark = [pytest.mark.functional, pytest.mark.fastapi, pytest.mark.anyio]


async def test_async_dependency_returns_empty_when_no_params_are_provided() -> (
    None
):
    """Returns an empty criteria object in an async FastAPI route."""
    app = FastAPI()
    dependency = criteria_dependency()

    @app.get("/items")
    async def list_items(
        criteria: Annotated[RequestCriteria, Depends(dependency)],
    ) -> dict[str, Any]:
        return {"is_empty": criteria.is_empty}

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/items")

    assert response.status_code == 200
    assert response.json() == {"is_empty": True}


async def test_async_dependency_parses_filter_sort_and_page_params() -> None:
    """Builds full request criteria from async FastAPI query params."""
    app = FastAPI()
    dependency = criteria_dependency(
        FastAPICriteriaConfig(default_page_size=25),
    )

    @app.get("/items")
    async def list_items(
        criteria: Annotated[RequestCriteria, Depends(dependency)],
    ) -> dict[str, Any]:
        page_request = criteria.page_request
        assert page_request is not None
        return {
            "query": (
                criteria.query.text if criteria.query is not None else None
            ),
            "sort": criteria.sort.text if criteria.sort is not None else None,
            "page": page_request.page_number,
            "size": page_request.page_size,
        }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/items",
            params={"filter": "name==demo", "sort": "name,asc"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "query": "name==demo",
        "sort": "name,asc",
        "page": 0,
        "size": 25,
    }


async def test_async_dependency_translates_semantic_errors_to_http_422() -> (
    None
):
    """Maps semantic failures to a stable HTTP 422 payload in async routes."""
    app = FastAPI()
    dependency = criteria_dependency(
        FastAPICriteriaConfig(
            query_options=QueryOptions(field_whitelist=frozenset({"name"})),
        ),
    )

    @app.get("/items")
    async def list_items(
        criteria: Annotated[RequestCriteria, Depends(dependency)],
    ) -> dict[str, bool]:
        return {"is_empty": criteria.is_empty}

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/items",
            params={"filter": "password==demo"},
        )

    assert response.status_code == 422
    payload = response.json()["detail"]
    assert payload["type"] == "urn:pyrsql:problem:query-semantic-error"
    assert payload["errors"][0]["code"] == "field_not_whitelisted"
    assert payload["errors"][0]["field"] == "password"
