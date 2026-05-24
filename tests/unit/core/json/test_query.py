"""Unit tests for ORM-neutral JSON query models."""

from __future__ import annotations

import pytest

from pyrsql.core.json.path import JSONPath
from pyrsql.core.json.query import JSONPathComparison
from pyrsql.core.json.values import DEFAULT_JSON_SCALAR_NORMALIZER


@pytest.mark.parametrize(
    ("path", "raw_arguments", "expected_value", "expected_literal"),
    [
        pytest.param(
            JSONPath(segments=("user", "id")),
            (("1", False),),
            1,
            "1",
            id="integer-argument",
        ),
        pytest.param(
            JSONPath(segments=("user", "active")),
            (("true", False),),
            True,
            "true",
            id="boolean-argument",
        ),
    ],
)
def test_json_path_comparison_normalizes_raw_arguments(
    path: JSONPath,
    raw_arguments: tuple[tuple[str, bool], ...],
    expected_value: object,
    expected_literal: str,
) -> None:
    """JSON comparisons normalize raw RSQL arguments through the core."""
    comparison = JSONPathComparison.from_raw_arguments(
        path=path,
        operator_name="equal",
        raw_arguments=raw_arguments,
    )

    assert comparison.path == path
    assert comparison.values[0].value == expected_value
    assert comparison.values[0].json_literal == expected_literal


def test_json_path_comparison_uses_shared_default_normalizer() -> None:
    """JSON comparisons reuse the shared default normalizer by default."""
    comparison = JSONPathComparison.from_raw_arguments(
        path=JSONPath(segments=("user", "active")),
        operator_name="equal",
        raw_arguments=(("true", False),),
    )
    expected = DEFAULT_JSON_SCALAR_NORMALIZER.normalize("true", quoted=False)

    assert comparison.values == (expected,)


def test_json_path_comparison_retains_normalized_payload() -> None:
    """JSON comparisons retain the normalized JSON comparison payload."""
    path = JSONPath(segments=("user", "id"))
    value = DEFAULT_JSON_SCALAR_NORMALIZER.normalize("1", quoted=False)
    comparison = JSONPathComparison(
        path=path,
        operator_name="equal",
        values=(value,),
    )

    assert comparison.path is path
    assert comparison.operator_name == "equal"
    assert comparison.values == (value,)
