"""Unit tests for FastAPI adapter configuration."""

from __future__ import annotations

import pytest

from pyrsql.adapters.fastapi import FastAPICriteriaConfig, SortParameterFormat
from pyrsql.core.options import QueryOptions, SortOptions

pytestmark = [pytest.mark.fastapi]


def test_config_exposes_derived_page_numbers() -> None:
    """Exposes derived one-based and zero-based page boundaries."""
    zero_based = FastAPICriteriaConfig()

    assert zero_based.minimum_page_number == 0
    assert zero_based.default_page_number == 0

    one_based = FastAPICriteriaConfig(one_based_paging=True)

    assert one_based.minimum_page_number == 1
    assert one_based.default_page_number == 1


def test_config_uses_semicolon_sort_format_by_default() -> None:
    """Preserves the single-parameter sort representation by default."""
    assert (
        FastAPICriteriaConfig().sort_parameter_format
        is SortParameterFormat.SEMICOLON
    )


def test_config_reuses_default_shared_options() -> None:
    """Keeps shared immutable defaults on the common path."""
    config = FastAPICriteriaConfig()

    assert isinstance(config.query_options, QueryOptions)
    assert isinstance(config.sort_options, SortOptions)
