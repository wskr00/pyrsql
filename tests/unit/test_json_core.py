"""Unit tests for backend-neutral JSON core primitives."""

import pytest

from pyrsql.core.json.path import JSONPath
from pyrsql.core.json.query import JSONPathComparison
from pyrsql.core.json.values import JSONScalarNormalizer


def test_json_path_rejects_empty_segments() -> None:
    """JSON paths reject empty path segments."""
    with pytest.raises(ValueError):
        JSONPath(("user", ""))


def test_json_path_reports_root_and_dot_path() -> None:
    """JSON paths expose root and dotted representations."""
    root_path = JSONPath()
    nested_path = JSONPath(("user", "id"))
    assert root_path.is_root is True
    assert nested_path.is_root is False
    assert nested_path.to_dot_path() == "user.id"


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
    assert normalizer.normalize("{\"id\": 1}", quoted=True).value == {
        "id": 1,
    }


def test_json_path_comparison_normalizes_raw_arguments() -> None:
    """JSON comparisons normalize raw RSQL arguments through the core."""
    comparison = JSONPathComparison.from_raw_arguments(
        path=JSONPath(("user", "id")),
        operator_name="equal",
        raw_arguments=(("1", False),),
    )
    assert comparison.path == JSONPath(("user", "id"))
    assert comparison.values[0].value == 1
    assert comparison.values[0].json_literal == "1"
