"""Functional tests for the FastAPI criteria dependency."""

from typing import Annotated, Any

import pytest

pytest.importorskip("fastapi")
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from pyrsql.adapters.fastapi import (
    CriteriaDependency,
    FastAPICriteriaConfig,
    RequestCriteria,
    SortParameterFormat,
    criteria_dependency,
)
from pyrsql.core.options import QueryOptions

pytestmark = [pytest.mark.functional, pytest.mark.fastapi]


def test_dependency_returns_empty_when_no_params_are_provided() -> None:
    """Returns an empty criteria object when the request has no query params."""
    app = FastAPI()
    dependency = criteria_dependency()

    @app.get("/items")
    def list_items(
        criteria: Annotated[RequestCriteria, Depends(dependency)],
    ) -> dict[str, Any]:
        return {"is_empty": criteria.is_empty}

    response = TestClient(app).get("/items")

    assert response.status_code == 200
    assert response.json() == {"is_empty": True}


def test_dependency_class_can_be_used_directly_with_depends() -> None:
    """Supports FastAPI's class-style callable dependency usage."""
    app = FastAPI()
    dependency = CriteriaDependency(FastAPICriteriaConfig(default_page_size=15))

    @app.get("/items")
    def list_items(
        criteria: Annotated[RequestCriteria, Depends(dependency)],
    ) -> dict[str, Any]:
        page_request = criteria.page_request
        assert page_request is not None
        return {
            "page": page_request.page_number,
            "size": page_request.page_size,
        }

    response = TestClient(app).get("/items")

    assert response.status_code == 200
    assert response.json() == {"page": 0, "size": 15}


def test_dependency_parses_filter_sort_and_page_params() -> None:
    """Builds full request criteria from FastAPI query parameters."""
    app = FastAPI()
    dependency = criteria_dependency(
        FastAPICriteriaConfig(default_page_size=25),
    )

    @app.get("/items")
    def list_items(
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

    response = TestClient(app).get(
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


def test_dependency_supports_repeated_sort_parameters() -> None:
    """Collects repeated sort parameters through FastAPI's list support."""
    app = FastAPI()
    dependency = criteria_dependency(
        FastAPICriteriaConfig(
            sort_parameter_format=SortParameterFormat.REPEATED,
        ),
    )

    @app.get("/items")
    def list_items(
        criteria: Annotated[RequestCriteria, Depends(dependency)],
    ) -> dict[str, str | None]:
        return {
            "sort": criteria.sort.text if criteria.sort is not None else None,
        }

    response = TestClient(app).get(
        "/items",
        params=[("sort", "name,asc"), ("sort", "created_at,desc")],
    )

    assert response.status_code == 200
    assert response.json() == {"sort": "name,asc;created_at,desc"}


def test_dependency_translates_query_parse_errors_to_http_400() -> None:
    """Maps query parsing failures to a stable HTTP 400 error payload."""
    app = FastAPI()
    dependency = criteria_dependency()

    @app.get("/items")
    def list_items(
        criteria: Annotated[RequestCriteria, Depends(dependency)],
    ) -> dict[str, bool]:
        return {"is_empty": criteria.is_empty}

    response = TestClient(app).get("/items", params={"filter": "name=="})

    assert response.status_code == 400
    payload = response.json()["detail"]
    assert payload["parameter"] == "filter"
    assert payload["type"] == "urn:pyrsql:problem:query-parse-error"
    assert payload["title"] == "Query parse error"
    assert payload["errors"][0]["code"] == "parse_error"
    assert payload["errors"][0]["location"] == {
        "index": 4,
        "line": 1,
        "column": 5,
    }


def test_dependency_exposes_structured_field_policy_diagnostics() -> None:
    """Publishes structured field diagnostics for blocked filter fields."""
    app = FastAPI()
    dependency = criteria_dependency(
        FastAPICriteriaConfig(
            query_options=QueryOptions(field_whitelist=frozenset({"name"})),
        ),
    )

    @app.get("/items")
    def list_items(
        criteria: Annotated[RequestCriteria, Depends(dependency)],
    ) -> dict[str, bool]:
        return {"is_empty": criteria.is_empty}

    response = TestClient(app).get(
        "/items",
        params={"filter": "password==demo"},
    )

    assert response.status_code == 422
    payload = response.json()["detail"]
    assert payload["type"] == "urn:pyrsql:problem:query-semantic-error"
    assert payload["errors"][0]["code"] == "field_not_whitelisted"
    assert payload["errors"][0]["field"] == "password"
    assert payload["errors"][0]["location"] == {
        "index": 0,
        "line": 1,
        "column": 1,
    }


def test_dependency_supports_one_based_paging() -> None:
    """Converts one-based request pages into zero-based PageRequest values."""
    app = FastAPI()
    dependency = criteria_dependency(
        FastAPICriteriaConfig(
            one_based_paging=True,
            default_page_size=20,
        ),
    )

    @app.get("/items")
    def list_items(
        criteria: Annotated[RequestCriteria, Depends(dependency)],
    ) -> dict[str, int | None]:
        page_request = criteria.page_request
        return {
            "page": (
                page_request.page_number if page_request is not None else None
            ),
            "size": (
                page_request.page_size if page_request is not None else None
            ),
        }

    response = TestClient(app).get("/items", params={"page": 2})

    assert response.status_code == 200
    assert response.json() == {"page": 1, "size": 20}


def test_dependency_honors_custom_parameter_names() -> None:
    """Uses configured aliases when extracting FastAPI query parameters."""
    app = FastAPI()
    dependency = criteria_dependency(
        FastAPICriteriaConfig(
            filter_parameter="where",
            sort_parameter="order",
            page_parameter="p",
            size_parameter="per_page",
            default_page_size=10,
            query_options=QueryOptions(strict_equality=True),
        ),
    )

    @app.get("/items")
    def list_items(
        criteria: Annotated[RequestCriteria, Depends(dependency)],
    ) -> dict[str, Any]:
        page_request = criteria.page_request
        assert criteria.query is not None
        return {
            "query": criteria.query.text,
            "strict_equality": criteria.query.options.strict_equality,
            "sort": criteria.sort.text if criteria.sort is not None else None,
            "page": (
                page_request.page_number if page_request is not None else None
            ),
            "size": (
                page_request.page_size if page_request is not None else None
            ),
        }

    response = TestClient(app).get(
        "/items",
        params={
            "where": "name==demo",
            "order": "name,desc",
            "p": 0,
            "per_page": 5,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "query": "name==demo",
        "strict_equality": True,
        "sort": "name,desc",
        "page": 0,
        "size": 5,
    }


def test_dependency_exposes_openapi_examples() -> None:
    """Publishes configured OpenAPI examples on query parameters."""
    app = FastAPI()
    dependency = criteria_dependency(
        FastAPICriteriaConfig(
            filter_openapi_examples={
                "by_name": {
                    "summary": "By name",
                    "value": "name==demo",
                },
            },
            sort_openapi_examples={
                "by_created_at": {
                    "summary": "By created_at desc",
                    "value": "created_at,desc",
                },
            },
        ),
    )

    @app.get("/items")
    def list_items(
        criteria: Annotated[RequestCriteria, Depends(dependency)],
    ) -> dict[str, bool]:
        return {"is_empty": criteria.is_empty}

    schema = app.openapi()
    parameters = schema["paths"]["/items"]["get"]["parameters"]
    parameter_map = {parameter["name"]: parameter for parameter in parameters}

    assert "examples" in parameter_map["filter"]
    assert (
        parameter_map["filter"]["examples"]["by_name"]["value"] == "name==demo"
    )
    assert "examples" in parameter_map["sort"]
