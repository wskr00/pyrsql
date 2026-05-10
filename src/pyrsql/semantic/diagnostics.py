"""Structured semantic diagnostics."""

from __future__ import annotations

from typing import TYPE_CHECKING

import msgspec

if TYPE_CHECKING:
    from pyrsql.parsing.source import SourceSpan


class SemanticDiagnostic(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """A structured semantic diagnostic."""

    code: str
    message: str
    span: SourceSpan

    def __str__(self) -> str:
        """Formats the diagnostic with source position data.

        Returns:
            The formatted diagnostic string.
        """
        return (
            f"[{self.code}] {self.message} at index {self.span.start.index} "
            f"(line {self.span.start.line}, column {self.span.start.column})"
        )
