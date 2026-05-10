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


@pytest.mark.parametrize(
    ("operator_name", "pattern"),
    [
        pytest.param("", r"cannot be empty", id="empty-operator-name"),
        pytest.param(
            " equal ",
            r"outer whitespace",
            id="whitespace-operator-name",
        ),
    ],
)
def test_json_path_comparison_rejects_invalid_operator_names(
    operator_name: str,
    pattern: str,
) -> None:
    """JSON comparisons reject invalid operator names."""
    with pytest.raises(ValueError, match=pattern):
        JSONPathComparison(
            path=JSONPath(segments=("user", "id")),
            operator_name=operator_name,
            values=(),
        )
