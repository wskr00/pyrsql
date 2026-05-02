"""Semantic expression nodes."""

from dataclasses import dataclass

from pyrsql.parsing.ast import Argument, LogicalOperator
from pyrsql.parsing.operators import ComparisonOperator
from pyrsql.parsing.source import SourceSpan
from pyrsql.selector.semantic import SemanticSelector


@dataclass(frozen=True, slots=True)
class SemanticNode:
    """Base semantic node."""

    span: SourceSpan


@dataclass(frozen=True, slots=True)
class SemanticComparison(SemanticNode):
    """Comparison expression after selector normalization."""

    selector: SemanticSelector
    operator: ComparisonOperator
    arguments: tuple[Argument, ...]


@dataclass(frozen=True, slots=True)
class SemanticLogical(SemanticNode):
    """Logical semantic node."""

    operator: LogicalOperator
    children: tuple["SemanticExpression", ...]


SemanticExpression = SemanticComparison | SemanticLogical
