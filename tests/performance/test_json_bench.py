"""Performance regression tests for JSON literal normalization."""

from __future__ import annotations

from timeit import timeit

import pytest

from pyrsql.core.json.query import JSONPathComparison
from pyrsql.core.json.values import DEFAULT_JSON_SCALAR_NORMALIZER

pytestmark = [pytest.mark.performance]

_QUOTED_JSON_OBJECT = '{"user":{"id":1,"name":"demo"},"active":true}'
_QUOTED_JSON_ARRAY = '[1,2,3,4,{"nested":true}]'


def test_quoted_json_object_normalization_remains_fast() -> None:
    """Keeps quoted JSON object normalization within budget."""
    elapsed = timeit(
        lambda: DEFAULT_JSON_SCALAR_NORMALIZER.normalize(
            _QUOTED_JSON_OBJECT,
            quoted=True,
        ),
        number=10_000,
    )
    average_microseconds = elapsed / 10_000 * 1_000_000
    assert average_microseconds < 100.0


def test_quoted_json_array_normalization_remains_fast() -> None:
    """Keeps quoted JSON array normalization within budget."""
    elapsed = timeit(
        lambda: DEFAULT_JSON_SCALAR_NORMALIZER.normalize(
            _QUOTED_JSON_ARRAY,
            quoted=True,
        ),
        number=10_000,
    )
    average_microseconds = elapsed / 10_000 * 1_000_000
    assert average_microseconds < 100.0


def test_json_path_comparison_build_remains_fast() -> None:
    """Keeps JSON path comparison normalization within budget."""
    elapsed = timeit(
        lambda: JSONPathComparison.from_raw_arguments(
            path=__import__("pyrsql").JSONPath(
                segments=("payload", "user", "id"),
            ),
            operator_name="equal",
            raw_arguments=((_QUOTED_JSON_OBJECT, True),),
        ),
        number=5_000,
    )
    average_microseconds = elapsed / 5_000 * 1_000_000
    assert average_microseconds < 200.0
