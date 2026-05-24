"""Bound logical query nodes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import msgspec

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pyrsql.parsing.ast import LogicalOperator
    from pyrsql.parsing.operators import ComparisonOperator
    from pyrsql.parsing.source import SourceSpan
    from pyrsql.selector.ast import SelectorLiteral

_MIN_LOGICAL_CHILDREN: Final = 2


class BoundNode(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Base class for bound logical nodes."""

    span: SourceSpan

    def walk(self) -> Iterator[BoundNode]:
        """Yields this node and all nested bound nodes depth-first."""
        yield self


class BoundSelectorNode(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Base class for bound selector nodes."""

    def walk_selectors(self) -> Iterator[BoundSelectorNode]:
        """Yields this selector and all nested selector nodes depth-first."""
        yield self


class BoundField(BoundSelectorNode, frozen=True, gc=False, kw_only=True):
    """A bound field selector after policy and mapping resolution."""

    raw_path: str
    field_path: str
    segments: tuple[str, ...]


class BoundLiteral(BoundSelectorNode, frozen=True, gc=False, kw_only=True):
    """A bound literal selector."""

    value: SelectorLiteral


class BoundFunction(BoundSelectorNode, frozen=True, gc=False, kw_only=True):
    """A bound function selector."""

    function_name: str
    arguments: tuple[BoundSelectorNode, ...]

    def walk_selectors(self) -> Iterator[BoundSelectorNode]:
        """Yields this selector and all nested selector nodes."""
        yield self
        for argument in self.arguments:
            yield from argument.walk_selectors()


class BoundArgument(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """A bound comparison argument.

    The argument remains intentionally raw at this stage. Type coercion still
    depends on later target-aware metadata.
    """

    text: str
    quoted: bool
    span: SourceSpan


class BoundComparison(BoundNode, frozen=True, gc=False, kw_only=True):
    """A bound comparison node."""

    selector: BoundSelectorNode
    operator: ComparisonOperator
    arguments: tuple[BoundArgument, ...]

    def __post_init__(self) -> None:
        """Validates bound comparison invariants.

        Raises:
            ValueError: If the arguments do not satisfy operator arity.
        """
        if len(self.arguments) < self.operator.minimum_arguments:
            raise ValueError(
                "Bound comparison is missing required operator arguments.",
            )
        if (
            self.operator.maximum_arguments is not None
            and len(self.arguments) > self.operator.maximum_arguments
        ):
            raise ValueError(
                "Bound comparison exceeds the operator argument limit.",
            )

    def walk(self) -> Iterator[BoundNode]:
        """Yields this comparison node."""
        yield self


class BoundLogical(BoundNode, frozen=True, gc=False, kw_only=True):
    """A bound logical node."""

    operator: LogicalOperator
    children: tuple[BoundNode, ...]

    def __post_init__(self) -> None:
        """Validates bound logical invariants.

        Raises:
            ValueError: If the logical node has fewer than two children.
        """
        if len(self.children) < _MIN_LOGICAL_CHILDREN:
            raise ValueError(
                "Bound logical nodes must contain at least two children.",
            )

    def walk(self) -> Iterator[BoundNode]:
        """Yields this node and all descendant nodes depth-first."""
        yield self
        for child in self.children:
            yield from child.walk()
