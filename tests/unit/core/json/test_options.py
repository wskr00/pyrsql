"""Unit tests for ORM-neutral JSON options."""

from __future__ import annotations

from typing import Any, cast

import pytest

from pyrsql.core.json.options import (
    DEFAULT_JSON_OPTIONS,
    JSONOptions,
    JSONSortScalarType,
)
from pyrsql.core.options import QueryOptions, SortOptions


@pytest.mark.parametrize(
    ("factory", "attribute_name"),
    [
        pytest.param(QueryOptions, "json_options", id="query-options"),
        pytest.param(SortOptions, "json_options", id="sort-options"),
    ],
)
def test_options_expose_default_json_options(
    factory: type[QueryOptions | SortOptions],
    attribute_name: str,
) -> None:
    """Query and sort options carry shared JSON options by default."""
    options = factory()

    assert getattr(options, attribute_name) is DEFAULT_JSON_OPTIONS


def test_query_options_accept_json_options_override() -> None:
    """Query options accept explicit JSON option overrides."""
    options = QueryOptions(json_options=JSONOptions(use_datetime=True))

    assert options.json_options.use_datetime is True


def test_json_options_accept_function_name_overrides() -> None:
    """JSON options expose configurable PostgreSQL function names."""
    options = JSONOptions(
        path_exists_function="custom_path_exists",
        path_exists_tz_function="custom_path_exists_tz",
    )

    assert options.path_exists_function == "custom_path_exists"
    assert options.path_exists_tz_function == "custom_path_exists_tz"


@pytest.mark.parametrize(
    ("kwargs", "pattern"),
    [
        pytest.param(
            {"path_exists_function": "bad-name"},
            r"valid SQL identifier",
            id="invalid-path-exists-function",
        ),
        pytest.param(
            {"path_exists_tz_function": " jsonb_path_exists_tz "},
            r"outer whitespace",
            id="whitespace-path-exists-tz-function",
        ),
        pytest.param(
            {"sort_field_types": cast("Any", "invalid")},
            r"sort_field_types",
            id="invalid-sort-field-types-mapping",
        ),
        pytest.param(
            {
                "sort_field_types": {
                    " payload.score ": JSONSortScalarType.NUMERIC,
                },
            },
            r"outer whitespace",
            id="whitespace-sort-field-path",
        ),
    ],
)
def test_json_options_reject_invalid_public_configuration(
    kwargs: dict[str, object],
    pattern: str,
) -> None:
    """JSON options reject malformed function names and sort config."""
    with pytest.raises((TypeError, ValueError), match=pattern):
        JSONOptions(**cast("Any", kwargs))


def test_json_options_normalize_sort_field_types() -> None:
    """JSON options normalize configured JSON sort scalar types."""
    options = JSONOptions(
        sort_field_types={"payload.score": cast("Any", "numeric")},
    )

    assert (
        options.sort_field_types["payload.score"] is JSONSortScalarType.NUMERIC
    )
