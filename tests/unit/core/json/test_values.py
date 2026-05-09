"""Unit tests for orm-neutral JSON value normalization."""

from pyrsql.core.json.values import JSONScalarNormalizer


def test_json_scalar_normalizer_parses_unquoted_scalars() -> None:
    """The normalizer parses booleans, nulls, and numbers."""
    normalizer = JSONScalarNormalizer()
    assert normalizer.normalize("true", quoted=False).value is True
    assert normalizer.normalize("null", quoted=False).value is None
    assert normalizer.normalize("42", quoted=False).value == 42
    assert normalizer.normalize("3.14", quoted=False).value == 3.14


def test_json_scalar_normalizer_parses_quoted_json_structures() -> None:
    """Quoted JSON arrays and objects are parsed as JSON values."""
    normalizer = JSONScalarNormalizer()
    assert normalizer.normalize("[1, 2]", quoted=True).value == [1, 2]
    assert normalizer.normalize('{"id": 1}', quoted=True).value == {
        "id": 1,
    }


def test_json_scalar_normalizer_parses_scientific_notation() -> None:
    """The normalizer parses exponent numbers as floats."""
    normalizer = JSONScalarNormalizer()
    assert normalizer.normalize("1e3", quoted=False).value == 1000.0
    assert normalizer.normalize("-2.5E-2", quoted=False).value == -0.025
