"""Performance regression tests for selector parsing."""

from __future__ import annotations

from timeit import timeit

import pytest

from pyrsql.selector.parser import DEFAULT_SELECTOR_PARSER

pytestmark = [pytest.mark.performance]

_FUNCTION_SELECTOR = "@concat[@upper[name]|#123|##raw]"


def test_selector_function_parse_remains_fast() -> None:
    """Keeps recursive selector parsing within a broad regression budget."""
    elapsed = timeit(
        lambda: DEFAULT_SELECTOR_PARSER.parse(
            _FUNCTION_SELECTOR,
            max_length=256,
            context="selector benchmark",
        ),
        number=10_000,
    )
    average_microseconds = elapsed / 10_000 * 1_000_000
    assert average_microseconds < 150.0
