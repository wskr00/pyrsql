"""Unit tests for FastAPI adapter configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import pytest

from pyrsql.adapters.fastapi import FastAPICriteriaConfig
from pyrsql.core.options import QueryOptions, SortOptions

if TYPE_CHECKING:
    from collections.abc import Mapping

pytestmark = [pytest.mark.fastapi]


@pytest.mark.parametrize(
    "kwargs",
    [
        pytest.param(
            {"filter_parameter": "filter", "sort_parameter": "filter"},
            id="duplicate-parameter-names",
        ),
        pytest.param(
            {"filter_parameter": " filter "},
            id="outer-whitespace",
        ),
    ],
)
def test_config_rejects_invalid_parameter_names(
    kwargs: dict[str, object],
) -> None:
    """Rejects duplicate aliases and names with outer whitespace."""
    with pytest.raises(ValueError, match=r"(?i)parameter|whitespace|unique"):
        FastAPICriteriaConfig(**cast("Any", kwargs))


@pytest.mark.parametrize(
    ("kwargs", "pattern"),
    [
        pytest.param(
            {"default_page_size": 0},
            r"default_page_size|page[_ ]?size|greater",
            id="non-positive-default-page-size",
        ),
        pytest.param(
            {"default_page_size": 51, "max_page_size": 50},
            r"max|page size|exceed",
            id="default-page-size-above-max",
        ),
        pytest.param(
            {"query_options": "invalid"},
            r"query_options",
            id="invalid-query-options",
        ),
        pytest.param(
            {"sort_options": "invalid"},
            r"sort_options",
            id="invalid-sort-options",
        ),
        pytest.param(
            {"filter_openapi_examples": "invalid"},
            r"filter_openapi_examples",
            id="invalid-filter-examples",
        ),
    ],
)
def test_config_rejects_invalid_public_configuration(
    kwargs: dict[str, object],
    pattern: str,
) -> None:
    """Rejects invalid paging, options, and OpenAPI examples."""
    with pytest.raises((TypeError, ValueError), match=pattern):
        FastAPICriteriaConfig(**cast("Any", kwargs))


def test_config_exposes_derived_page_numbers() -> None:
    """Exposes derived one-based and zero-based page boundaries."""
    zero_based = FastAPICriteriaConfig()

    assert zero_based.minimum_page_number == 0
    assert zero_based.default_page_number == 0

    one_based = FastAPICriteriaConfig(one_based_paging=True)

    assert one_based.minimum_page_number == 1
    assert one_based.default_page_number == 1


def test_config_keeps_openapi_examples_as_immutable_copies(
    openapi_examples: Mapping[str, Any],
) -> None:
    """Stores OpenAPI examples as immutable copies."""
    config = FastAPICriteriaConfig(filter_openapi_examples=openapi_examples)

    assert config.filter_openapi_examples["by_name"]["value"] == "name==demo"
    assert config.filter_openapi_examples is not openapi_examples

    with pytest.raises(TypeError):
        cast("dict[str, Any]", config.filter_openapi_examples)["new"] = {}


def test_config_reuses_default_shared_options() -> None:
    """Keeps shared immutable defaults on the common path."""
    config = FastAPICriteriaConfig()

    assert isinstance(config.query_options, QueryOptions)
    assert isinstance(config.sort_options, SortOptions)
