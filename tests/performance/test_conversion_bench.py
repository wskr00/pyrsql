"""Performance regression tests for core value conversion."""

from __future__ import annotations

import datetime as dt
from timeit import timeit

import pytest

from pyrsql.core.conversion import DEFAULT_VALUE_CONVERTER_REGISTRY

from .conftest import DATE_TEXT, DATETIME_TEXT

pytestmark = [pytest.mark.performance]


def test_datetime_conversion_remains_fast() -> None:
    """Keeps ISO datetime conversion within a broad regression budget."""
    elapsed = timeit(
        lambda: DEFAULT_VALUE_CONVERTER_REGISTRY.convert(
            DATETIME_TEXT,
            dt.datetime,
        ),
        number=10_000,
    )
    average_microseconds = elapsed / 10_000 * 1_000_000
    assert average_microseconds < 50.0


def test_date_to_datetime_fallback_remains_fast() -> None:
    """Keeps LocalDate-style datetime fallback within budget."""
    elapsed = timeit(
        lambda: DEFAULT_VALUE_CONVERTER_REGISTRY.convert(
            DATE_TEXT,
            dt.datetime,
        ),
        number=10_000,
    )
    average_microseconds = elapsed / 10_000 * 1_000_000
    assert average_microseconds < 50.0
