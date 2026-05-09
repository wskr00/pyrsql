"""Bound logical query nodes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import msgspec

from pyrsql.parsing.source import SourceSpan

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pyrsql.parsing.ast import LogicalOperator
    from pyrsql.parsing.operators import ComparisonOperator
    from pyrsql.selector.ast import SelectorLiteral


class BoundNode(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Base class for bound logical nodes."""

    span: SourceSpan

    def __post_init__(self) -> None:
        """Validates bound node invariants.

        Raises:
            TypeError: If the span is not a SourceSpan.
        """
        if not isinstance(self.span, SourceSpan):
            raise TypeError("Bound node span must be a SourceSpan.")

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

    def __post_init__(self) -> None:
        """Validates bound field invariants.

        Raises:
            ValueError: If the raw path, field path, or segments are invalid.
        """
        if not self.raw_path:
            raise ValueError("Bound field raw_path cannot be empty.")
        if not self.field_path:
            raise ValueError("Bound field field_path cannot be empty.")
        if not self.segments:
            raise ValueError("Bound field must contain at least one segment.")
        if tuple(self.field_path.split(".")) != self.segments:
            raise ValueError(
                "Bound field segments must match the resolved field_path.",
            )


class BoundLiteral(BoundSelectorNode, frozen=True, gc=False, kw_only=True):
    """A bound literal selector."""

    value: SelectorLiteral


class BoundFunction(BoundSelectorNode, frozen=True, gc=False, kw_only=True):
    """A bound function selector."""

    function_name: str
    arguments: tuple[BoundSelectorNode, ...]

    def __post_init__(self) -> None:
        """Validates bound function invariants.

        Raises:
            ValueError: If the function name or arguments are invalid.
        """
        if not self.function_name:
            raise ValueError("Bound function name cannot be empty.")
        if not self.arguments:
            raise ValueError(
                "Bound function must contain at least one argument.",
            )

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

    def __post_init__(self) -> None:
        """Validates bound argument invariants.

        Raises:
            TypeError: If the argument text or span has the wrong type.
        """
        if not isinstance(self.text, str):
            raise TypeError("Bound argument text must be a string.")
        if not isinstance(self.span, SourceSpan):
            raise TypeError("Bound argument span must be a SourceSpan.")


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
        super().__post_init__()
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
        super().__post_init__()
        if len(self.children) < 2:
            raise ValueError(
                "Bound logical nodes must contain at least two children.",
            )

    def walk(self) -> Iterator[BoundNode]:
        """Yields this node and all descendant nodes depth-first."""
        yield self
        for child in self.children:
            yield from child.walk()
