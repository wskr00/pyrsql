"""AST node definitions for pyrsql parsing."""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

import msgspec

if TYPE_CHECKING:
    from pyrsql.parsing.operators import ComparisonOperator
    from pyrsql.parsing.source import SourceSpan
    from pyrsql.selector.ast import SelectorNode


class Argument(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Represents a comparison argument."""

    text: str
    quoted: bool
    span: SourceSpan


class ComparisonNode(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Leaf node for selector/operator/arguments expressions."""

    span: SourceSpan
    selector: SelectorNode
    operator: ComparisonOperator
    arguments: tuple[Argument, ...]

    def with_span(self, span: SourceSpan) -> ComparisonNode:
        """Returns a copy of the comparison with an updated span.

        Returns:
            A comparison node copy with the provided span.
        """
        return ComparisonNode(
            span=span,
            selector=self.selector,
            operator=self.operator,
            arguments=self.arguments,
        )


class LogicalOperator(Enum):
    """Logical operators supported in the AST."""

    AND = auto()
    OR = auto()


class LogicalNode(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Logical expression with two or more child nodes."""

    span: SourceSpan
    operator: LogicalOperator
    children: tuple[Expression, ...]

    def with_span(self, span: SourceSpan) -> LogicalNode:
        """Returns a copy of the logical node with an updated span.

        Returns:
            A logical node copy with the provided span.
        """
        return LogicalNode(
            span=span,
            operator=self.operator,
            children=self.children,
        )


Expression = ComparisonNode | LogicalNode
