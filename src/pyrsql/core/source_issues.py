"""Shared source-location-aware diagnostics and errors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

import msgspec

if TYPE_CHECKING:
    from pyrsql.parsing.source import SourceSpan


class SourceDiagnostic(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Structured diagnostic tied to one source span."""

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


@dataclass(frozen=True, slots=True)
class SourceError(ValueError):
    """Base exception for failures tied to one source span."""

    message: str
    span: SourceSpan
    code: ClassVar[str] = "source_error"
    diagnostic_type: ClassVar[type[SourceDiagnostic]] = SourceDiagnostic

    @property
    def diagnostic(self) -> SourceDiagnostic:
        """Returns the structured diagnostic for this error.

        Returns:
            The structured source diagnostic.
        """
        return self.diagnostic_type(
            code=self.code,
            message=self.message,
            span=self.span,
        )

    def __str__(self) -> str:
        """Formats the error with source location data.

        Returns:
            The formatted error string.
        """
        return (
            f"[{self.code}] {self.message} at index {self.span.start.index} "
            f"(line {self.span.start.line}, column {self.span.start.column})"
        )
