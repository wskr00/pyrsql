"""Unit tests for bound logical query nodes."""

from __future__ import annotations

import pytest

from pyrsql.ir.query import (
    BoundArgument,
    BoundComparison,
    BoundField,
    BoundFunction,
    BoundLiteral,
    BoundLogical,
)
from pyrsql.parsing.ast import LogicalOperator
from pyrsql.parsing.operators import EQUAL
from pyrsql.parsing.source import SourcePosition, SourceSpan


def _span() -> SourceSpan:
    """Builds a reusable test span."""
    return SourceSpan(
        start=SourcePosition(index=0, line=1, column=1),
        end=SourcePosition(index=4, line=1, column=5),
    )


def _bound_field(raw_path: str, field_path: str) -> BoundField:
    """Builds a simple bound field for tests."""
    return BoundField(
        raw_path=raw_path,
        field_path=field_path,
        segments=tuple(field_path.split(".")),
    )


def _bound_comparison(
    raw_path: str,
    field_path: str,
    argument: str,
) -> BoundComparison:
    """Builds a simple bound comparison for tests."""
    return BoundComparison(
        span=_span(),
        selector=_bound_field(raw_path, field_path),
        operator=EQUAL,
        arguments=(BoundArgument(text=argument, quoted=False, span=_span()),),
    )


def test_bound_field_keeps_raw_and_resolved_paths() -> None:
    """Stores both the original and resolved field paths."""
    selector = _bound_field("username", "user.name")

    assert selector.raw_path == "username"
    assert selector.field_path == "user.name"
    assert selector.segments == ("user", "name")


def test_bound_function_walks_nested_selectors() -> None:
    """Traverses nested selector trees depth-first."""
    selector = BoundFunction(
        function_name="upper",
        arguments=(
            _bound_field("username", "user.name"),
            BoundLiteral(value=True),
        ),
    )
    walked = tuple(selector.walk_selectors())

    assert walked[0] is selector
    assert isinstance(walked[1], BoundField)
    assert isinstance(walked[2], BoundLiteral)


def test_bound_logical_walks_descendants_depth_first() -> None:
    """Traverses the logical expression tree depth-first."""
    first_child = _bound_comparison("username", "user.name", "demo")
    second_child = _bound_comparison("city", "city", "sp")
    expression = BoundLogical(
        span=_span(),
        operator=LogicalOperator.AND,
        children=(first_child, second_child),
    )
    walked = tuple(expression.walk())

    assert walked == (expression, first_child, second_child)


@pytest.mark.parametrize(
    ("factory", "pattern"),
    [
        pytest.param(
            lambda: BoundField(
                raw_path="username",
                field_path="user.name",
                segments=("user",),
            ),
            r"segments must match",
            id="field-segments-mismatch",
        ),
        pytest.param(
            lambda: BoundFunction(function_name="upper", arguments=()),
            r"at least one argument",
            id="function-without-arguments",
        ),
        pytest.param(
            lambda: BoundLogical(
                span=_span(),
                operator=LogicalOperator.AND,
                children=(_bound_comparison("username", "user.name", "demo"),),
            ),
            r"at least two children",
            id="logical-single-child",
        ),
    ],
)
def test_bound_query_nodes_reject_invalid_construction(
    factory: object,
    pattern: str,
) -> None:
    """Rejects invalid bound query node invariants."""
    with pytest.raises(ValueError, match=pattern):
        factory()  # type: ignore[operator]
