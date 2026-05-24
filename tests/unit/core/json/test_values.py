"""Unit tests for ORM-neutral JSON value normalization."""

from __future__ import annotations

import pytest

from pyrsql.core.json.values import JSONScalarNormalizer


@pytest.mark.parametrize(
    ("raw_value", "quoted", "expected"),
    [
        pytest.param("true", False, True, id="bool-true"),
        pytest.param("null", False, None, id="null"),
        pytest.param("42", False, 42, id="int"),
        pytest.param("3.12", False, 3.12, id="float"),
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


@pytest.mark.parametrize(
    ("raw_value", "expected_literal"),
    [
        pytest.param("true", '"true"', id="quoted-bool"),
        pytest.param("null", '"null"', id="quoted-null"),
        pytest.param("123", '"123"', id="quoted-int"),
        pytest.param("3.14", '"3.14"', id="quoted-float"),
    ],
)
def test_json_scalar_normalizer_keeps_quoted_scalars_as_strings(
    raw_value: str,
    expected_literal: str,
) -> None:
    """Quoted scalar literals remain strings instead of coercing as JSON."""
    normalized = JSONScalarNormalizer().normalize(raw_value, quoted=True)

    assert normalized.value == raw_value
    assert normalized.json_literal == expected_literal
    assert normalized.python_type is str


@pytest.mark.parametrize(
    ("raw_value", "expected_value", "expected_literal"),
    [
        pytest.param("1e309", "1e309", '"1e309"', id="out-of-range-float"),
        pytest.param("01", "01", '"01"', id="invalid-json-leading-zero"),
    ],
)
def test_json_scalar_normalizer_keeps_invalid_json_numbers_as_strings(
    raw_value: str,
    expected_value: str,
    expected_literal: str,
) -> None:
    """Invalid JSON numbers remain plain strings instead of coercing badly."""
    normalized = JSONScalarNormalizer().normalize(raw_value, quoted=False)

    assert normalized.value == expected_value
    assert normalized.json_literal == expected_literal
    assert normalized.python_type is str
