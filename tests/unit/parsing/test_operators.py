"""Unit tests for parsing operator models."""

from __future__ import annotations

import pytest

from pyrsql.parsing.operators import ComparisonOperator, OperatorRegistry


@pytest.mark.parametrize(
    ("kwargs", "pattern"),
    [
        pytest.param(
            {
                "name": None,
                "spellings": ("==",),
                "minimum_arguments": 1,
                "maximum_arguments": 1,
            },
            r"name must be a string",
            id="non-string-name",
        ),
        pytest.param(
            {
                "name": " equal ",
                "spellings": ("==",),
                "minimum_arguments": 1,
                "maximum_arguments": 1,
            },
            r"outer whitespace",
            id="whitespace-name",
        ),
        pytest.param(
            {
                "name": "equal",
                "spellings": ["=="],
                "minimum_arguments": 1,
                "maximum_arguments": 1,
            },
            r"tuple of strings",
            id="non-tuple-spellings",
        ),
        pytest.param(
            {
                "name": "equal",
                "spellings": (" =eq= ",),
                "minimum_arguments": 1,
                "maximum_arguments": 1,
            },
            r"outer whitespace",
            id="whitespace-spelling",
        ),
        pytest.param(
            {
                "name": "equal",
                "spellings": ("==",),
                "minimum_arguments": True,
                "maximum_arguments": 1,
            },
            r"minimum_arguments",
            id="bool-minimum-arguments",
        ),
    ],
)
def test_comparison_operator_rejects_invalid_runtime_payloads(
    kwargs: dict[str, object],
    pattern: str,
) -> None:
    """Comparison operators enforce a strict runtime contract."""
    with pytest.raises((TypeError, ValueError), match=pattern):
        ComparisonOperator(**kwargs)


@pytest.mark.parametrize(
    ("kwargs", "pattern"),
    [
        pytest.param(
            {"operators": ["bad"]},
            r"tuple of ComparisonOperator",
            id="non-tuple-operators",
        ),
        pytest.param(
            {
                "operators": (
                    ComparisonOperator(
                        name="equal",
                        spellings=("==",),
                        minimum_arguments=1,
                        maximum_arguments=1,
                    ),
                    "bad",
                ),
            },
            r"ComparisonOperator instances",
            id="invalid-operator-entry",
        ),
    ],
)
def test_operator_registry_rejects_invalid_runtime_payloads(
    kwargs: dict[str, object],
    pattern: str,
) -> None:
    """Operator registries enforce a strict runtime contract."""
    with pytest.raises((TypeError, ValueError), match=pattern):
        OperatorRegistry(**kwargs)
