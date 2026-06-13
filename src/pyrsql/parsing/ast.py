"""AST node definitions for pyrsql parsing."""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

import msgspec

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pyrsql.parsing.operators import ComparisonOperator
    from pyrsql.parsing.source import SourceSpan
    from pyrsql.selector.ast import SelectorNode


class Argument(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Represents a comparison argument."""

    text: str
    quoted: bool
    span: SourceSpan


class Node(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Base AST node."""

    span: SourceSpan

    def walk(self) -> Iterator[Node]:
        """Yields this node and all nested syntax nodes depth-first."""
        yield self


class ComparisonNode(Node, frozen=True, gc=False, kw_only=True):
    """Leaf node for selector/operator/arguments expressions."""

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


class LogicalNode(Node, frozen=True, gc=False, kw_only=True):
    """Logical expression with two or more child nodes."""

    operator: LogicalOperator
    children: tuple[Expression, ...]

    def walk(self) -> Iterator[Node]:
        """Yields this node and all descendant syntax nodes depth-first."""
        yield self
        for child in self.children:
            yield from child.walk()

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
