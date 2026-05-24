"""Syntax nodes for shared pyrsql selectors."""

from __future__ import annotations

from typing import TYPE_CHECKING

import msgspec

if TYPE_CHECKING:
    from collections.abc import Iterator

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


class LiteralSelector(SelectorNode, frozen=True, gc=False, kw_only=True):
    """Static literal selector."""

    value: SelectorLiteral


class FunctionSelector(SelectorNode, frozen=True, gc=False, kw_only=True):
    """Function selector."""

    function_name: str
    arguments: tuple[SelectorNode, ...]

    def walk(self) -> Iterator[SelectorNode]:
        """Yields this selector and all nested selectors depth-first."""
        yield self
        for argument in self.arguments:
            yield from argument.walk()
