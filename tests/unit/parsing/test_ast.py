"""Unit tests for parsing AST models."""

from __future__ import annotations

from pyrsql.parsing.ast import (
    ComparisonNode,
    LogicalNode,
    LogicalOperator,
)
from pyrsql.parsing.operators import EQUAL
from pyrsql.parsing.source import SourcePosition, SourceSpan
from pyrsql.selector.ast import FieldSelector


def _span() -> SourceSpan:
    """Builds one valid source span for AST tests."""
    return SourceSpan(
        start=SourcePosition(index=0, line=1, column=1),
        end=SourcePosition(index=4, line=1, column=5),
    )


def test_comparison_node_with_span_reuses_existing_payload() -> None:
    """Comparison nodes can be copied with a replacement span."""
    original = ComparisonNode(
        span=_span(),
        selector=FieldSelector(raw_path="name"),
        operator=EQUAL,
        arguments=(),
    )
    replacement = SourceSpan(
        start=SourcePosition(index=10, line=2, column=1),
        end=SourcePosition(index=14, line=2, column=5),
    )

    copied = original.with_span(replacement)

    assert copied.span == replacement
    assert copied.selector is original.selector
    assert copied.operator is original.operator
    assert copied.arguments is original.arguments


def test_logical_node_with_span_reuses_existing_children() -> None:
    """Logical nodes can be copied with a replacement span."""
    child = ComparisonNode(
        span=_span(),
        selector=FieldSelector(raw_path="name"),
        operator=EQUAL,
        arguments=(),
    )
    original = LogicalNode(
        span=_span(),
        operator=LogicalOperator.AND,
        children=(child,),
    )
    replacement = SourceSpan(
        start=SourcePosition(index=10, line=2, column=1),
        end=SourcePosition(index=20, line=2, column=11),
    )

    copied = original.with_span(replacement)

    assert copied.span == replacement
    assert copied.operator is original.operator
    assert copied.children is original.children
