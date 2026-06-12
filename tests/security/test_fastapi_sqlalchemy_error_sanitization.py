"""Security tests for non-verbose error handling at the API edge."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pyrsql.adapters.fastapi import FastAPICriteriaConfig
from pyrsql.core.options import QueryOptions, SortOptions
from pyrsql.parsing.limits import ParseLimits
from pyrsql.sorting.limits import SortLimits
from tests.security.conftest import assert_response_hides_internal_error_details

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


def test_backend_query_errors_do_not_leak_stack_traces(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Returns one controlled 422 payload instead of verbose backend errors."""
    response = integration_app_factory().get(
        "/users",
        params={"filter": "password==demo"},
    )

    assert response.status_code == 422
    assert_response_hides_internal_error_details(response)


def test_backend_sort_errors_do_not_leak_stack_traces(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Returns one controlled 422 payload for invalid sort backend errors."""
    response = integration_app_factory().get(
        "/users",
        params={"sort": "DROP TABLE users"},
    )

    assert response.status_code == 422
    assert_response_hides_internal_error_details(response)


def test_query_parse_errors_do_not_leak_internal_details(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Keeps parse failures structured without exposing internal paths."""
    response = integration_app_factory(
        criteria_config=FastAPICriteriaConfig(
            query_options=QueryOptions(
                parse_limits=ParseLimits(max_query_length=9),
            ),
        ),
    ).get(
        "/users",
        params={"filter": "name=='demo'"},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["type"] == QUERY_PARSE_TYPE
    assert_response_hides_internal_error_details(response)


def test_composed_hostile_request_fails_cleanly_at_first_limit(
    integration_app_factory: Callable[..., TestClient],
) -> None:
    """Fails cleanly on the earliest query limit even with multiple attacks."""
    response = integration_app_factory(
        criteria_config=FastAPICriteriaConfig(
            query_options=QueryOptions(
                parse_limits=ParseLimits(max_query_length=20),
            ),
            sort_options=SortOptions(
                sort_limits=SortLimits(max_sort_length=5),
            ),
            max_page_size=5,
        ),
    ).get(
        "/users",
        params={
            "filter": "name==demo;company.name==acme",
            "sort": "company.name,desc",
            "size": "5",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["type"] == QUERY_PARSE_TYPE
    assert_response_hides_internal_error_details(response)
