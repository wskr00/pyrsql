"""Performance regression tests for core value conversion."""

from __future__ import annotations

from timeit import timeit

import pytest

from pyrsql.core.conversion import DEFAULT_VALUE_CONVERTER_REGISTRY

pytestmark = [pytest.mark.performance]

_DATETIME_TEXT = "2026-05-02T10:30:45.123456+00:00"
_DATE_TEXT = "2026-05-02"


def test_datetime_conversion_remains_fast() -> None:
    """Keeps ISO datetime conversion within a broad regression budget."""
    elapsed = timeit(
        lambda: DEFAULT_VALUE_CONVERTER_REGISTRY.convert(
            _DATETIME_TEXT,
            __import__("datetime").datetime,
        ),
        number=10_000,
    )
    average_microseconds = elapsed / 10_000 * 1_000_000
    assert average_microseconds < 50.0


def test_date_to_datetime_fallback_remains_fast() -> None:
    """Keeps LocalDate-style datetime fallback within budget."""
    elapsed = timeit(
        lambda: DEFAULT_VALUE_CONVERTER_REGISTRY.convert(
            _DATE_TEXT,
            __import__("datetime").datetime,
        ),
        number=10_000,
    )
    average_microseconds = elapsed / 10_000 * 1_000_000
    assert average_microseconds < 50.0
