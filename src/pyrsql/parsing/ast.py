"""AST node definitions for pyrsql parsing."""

from dataclasses import dataclass
from enum import Enum
from enum import auto

from pyrsql.parsing.operators import ComparisonOperator
from pyrsql.parsing.source import SourceSpan


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


@dataclass(frozen=True, slots=True)
class ComparisonNode(Node):
    """Leaf node for selector/operator/arguments expressions."""

    selector: str
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
    children: tuple[Node, ...]
