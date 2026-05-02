"""Unit tests for FastAPI adapter configuration."""

import pytest

from pyrsql.adapters.fastapi import FastAPICriteriaConfig

pytestmark = [pytest.mark.unit, pytest.mark.fastapi]


def test_config_rejects_duplicate_parameter_names() -> None:
    """Rejects duplicate FastAPI query parameter aliases."""
    with pytest.raises(ValueError):
        FastAPICriteriaConfig(
            filter_parameter="filter",
            sort_parameter="filter",
        )


def test_config_rejects_non_positive_default_page_size() -> None:
    """Rejects invalid default page size values."""
    with pytest.raises(ValueError):
        FastAPICriteriaConfig(default_page_size=0)


def test_config_rejects_default_page_size_above_max() -> None:
    """Rejects inconsistent page size defaults and limits."""
    with pytest.raises(ValueError):
        FastAPICriteriaConfig(default_page_size=51, max_page_size=50)


def test_config_exposes_derived_page_numbers() -> None:
    """Exposes derived one-based and zero-based page boundaries."""
    assert FastAPICriteriaConfig().minimum_page_number == 0
    assert FastAPICriteriaConfig().default_page_number == 0
    one_based = FastAPICriteriaConfig(one_based_paging=True)
    assert one_based.minimum_page_number == 1
    assert one_based.default_page_number == 1
