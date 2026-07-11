"""Syntax nodes for shared pyrsql selectors."""

from __future__ import annotations

from typing import TypeAlias

import msgspec

SelectorLiteral = str | int | float | bool | None


class FieldSelector(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Field-path selector as written in the source text."""

    raw_path: str


class LiteralSelector(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Static literal selector."""

    value: SelectorLiteral


class FunctionSelector(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Function selector."""

    function_name: str
    arguments: tuple[SelectorNode, ...]


SelectorNode: TypeAlias = FieldSelector | LiteralSelector | FunctionSelector
