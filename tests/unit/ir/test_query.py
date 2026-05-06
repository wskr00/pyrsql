"""Unit tests for bound logical query nodes."""

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
    return SourceSpan(
        start=SourcePosition(index=0, line=1, column=1),
        end=SourcePosition(index=4, line=1, column=5),
    )


def test_bound_field_keeps_raw_and_resolved_paths() -> None:
    """Stores both the original and resolved field paths."""
    selector = BoundField(
        raw_path="username",
        field_path="user.name",
        segments=("user", "name"),
    )
    assert selector.raw_path == "username"
    assert selector.field_path == "user.name"
    assert selector.segments == ("user", "name")


def test_bound_function_walks_nested_selectors() -> None:
    """Traverses nested selector trees depth-first."""
    selector = BoundFunction(
        function_name="upper",
        arguments=(
            BoundField(
                raw_path="username",
                field_path="user.name",
                segments=("user", "name"),
            ),
            BoundLiteral(value=True),
        ),
    )
    walked = tuple(selector.walk_selectors())
    assert walked[0] is selector
    assert isinstance(walked[1], BoundField)
    assert isinstance(walked[2], BoundLiteral)


def test_bound_logical_walks_descendants_depth_first() -> None:
    """Traverses the logical expression tree depth-first."""
    child = BoundComparison(
        span=_span(),
        selector=BoundField(
            raw_path="username",
            field_path="user.name",
            segments=("user", "name"),
        ),
        operator=EQUAL,
        arguments=(BoundArgument(text="demo", quoted=False, span=_span()),),
    )
    expression = BoundLogical(
        span=_span(),
        operator=LogicalOperator.AND,
        children=(child,),
    )
    walked = tuple(expression.walk())
    assert walked == (expression, child)
