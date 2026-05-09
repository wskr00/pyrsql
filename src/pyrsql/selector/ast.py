"""Syntax nodes for shared pyrsql selectors."""

from __future__ import annotations

from collections.abc import Iterator

import msgspec

SelectorLiteral = str | int | float | bool | None


class SelectorNode(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Base class for selector syntax nodes."""

    def walk(self) -> Iterator[SelectorNode]:
        """Yields this selector and all nested selectors depth-first."""
        yield self


class FieldSelector(SelectorNode, frozen=True, gc=False, kw_only=True):
    """Field-path selector as written in the source text."""

    raw_path: str
    segments: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validates field selector invariants."""
        if not self.raw_path:
            raise ValueError("Field selector path cannot be empty.")
        if self.raw_path != self.raw_path.strip():
            raise ValueError(
                "Field selector path cannot contain outer whitespace."
            )
        if not self.segments:
            raise ValueError(
                "Field selector must contain at least one segment."
            )
        if any(not segment for segment in self.segments):
            raise ValueError(
                "Field selector cannot contain empty path segments."
            )
        if tuple(self.raw_path.split(".")) != self.segments:
            raise ValueError("Field selector segments must match the raw path.")


class LiteralSelector(SelectorNode, frozen=True, gc=False, kw_only=True):
    """Static literal selector."""

    value: SelectorLiteral


class FunctionSelector(SelectorNode, frozen=True, gc=False, kw_only=True):
    """Function selector."""

    function_name: str
    arguments: tuple[SelectorNode, ...]

    def __post_init__(self) -> None:
        """Validates function selector invariants."""
        if not self.function_name:
            raise ValueError("Function selector name cannot be empty.")
        if self.function_name != self.function_name.strip():
            raise ValueError(
                "Function selector name cannot contain outer whitespace."
            )
        if not self.arguments:
            raise ValueError(
                "Function selector must contain at least one argument."
            )

    def walk(self) -> Iterator[SelectorNode]:
        """Yields this selector and all nested selectors depth-first."""
        yield self
        for argument in self.arguments:
            yield from argument.walk()
