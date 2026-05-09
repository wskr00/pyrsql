"""Unit tests for orm-neutral JSON query models."""

from pyrsql.core.json.path import JSONPath
from pyrsql.core.json.query import JSONPathComparison
from pyrsql.core.json.values import DEFAULT_JSON_SCALAR_NORMALIZER


def test_json_path_comparison_normalizes_raw_arguments() -> None:
    """JSON comparisons normalize raw RSQL arguments through the core."""
    comparison = JSONPathComparison.from_raw_arguments(
        path=JSONPath(segments=("user", "id")),
        operator_name="equal",
        raw_arguments=(("1", False),),
    )
    assert comparison.path == JSONPath(segments=("user", "id"))
    assert comparison.values[0].value == 1
    assert comparison.values[0].json_literal == "1"


def test_json_path_comparison_uses_shared_default_normalizer() -> None:
    """JSON comparisons reuse the shared default normalizer by default."""
    comparison = JSONPathComparison.from_raw_arguments(
        path=JSONPath(segments=("user", "active")),
        operator_name="equal",
        raw_arguments=(("true", False),),
    )
    expected = DEFAULT_JSON_SCALAR_NORMALIZER.normalize("true", quoted=False)
    assert comparison.values == (expected,)
