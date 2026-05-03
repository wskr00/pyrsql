"""AST node definitions for pyrsql parsing."""

import sys
from dataclasses import dataclass, replace
from enum import Enum, auto

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from pyrsql.parsing.operators import ComparisonOperator
from pyrsql.parsing.source import SourceSpan
from pyrsql.selector.ast import Selector


@dataclass(frozen=True, slots=True)
class Argument:
    """Represents a comparison argument."""

    text: str
    quoted: bool
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class Node:
    """Base AST node."""

    span: SourceSpan

    def with_span(self, span: SourceSpan) -> Self:
        """Returns a copy of the node with an updated source span."""
        return replace(self, span=span)


@dataclass(frozen=True, slots=True)
class ComparisonNode(Node):
    """Leaf node for selector/operator/arguments expressions."""

    selector: Selector
    operator: ComparisonOperator
    arguments: tuple[Argument, ...]


class LogicalOperator(Enum):
    """Logical operators supported in the AST."""

    AND = auto()
    OR = auto()


@dataclass(frozen=True, slots=True)
class LogicalNode(Node):
    """Logical expression with two or more child nodes."""

    operator: LogicalOperator
    children: tuple["Expression", ...]


Expression = ComparisonNode | LogicalNode
