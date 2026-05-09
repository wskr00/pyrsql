"""Unit tests for ORM-neutral JSON value normalization."""

from __future__ import annotations

import math

import pytest

from pyrsql.core.json.values import JSONScalarNormalizer


@pytest.mark.parametrize(
    ("raw_value", "quoted", "expected"),
    [
        pytest.param("true", False, True, id="bool-true"),
        pytest.param("null", False, None, id="null"),
        pytest.param("42", False, 42, id="int"),
        pytest.param("3.14", False, math.pi, id="float"),
        pytest.param("1e3", False, 1000.0, id="scientific-positive"),
        pytest.param("-2.5E-2", False, -0.025, id="scientific-negative"),
        pytest.param("[1, 2]", True, [1, 2], id="quoted-array"),
        pytest.param('{"id": 1}', True, {"id": 1}, id="quoted-object"),
    ],
)
def test_json_scalar_normalizer_parses_supported_values(
    raw_value: str,
    quoted: bool,
    expected: object,
) -> None:
    """The normalizer parses scalar and structured JSON values."""
    normalizer = JSONScalarNormalizer()

    assert normalizer.normalize(raw_value, quoted=quoted).value == expected
