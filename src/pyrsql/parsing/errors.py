"""Parsing error types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from pyrsql.parsing.diagnostics import ParseDiagnostic

if TYPE_CHECKING:
    from pyrsql.parsing.source import SourceSpan


@dataclass(frozen=True, slots=True)
class ParseError(ValueError):
    """Base exception for parsing failures."""

    message: str
    span: SourceSpan
    code: ClassVar[str] = "parse_error"

    @property
    def diagnostic(self) -> ParseDiagnostic:
        """Returns the structured diagnostic for this error.

        Returns:
            The structured parse diagnostic.
        """
        return ParseDiagnostic(
            code=self.code,
            message=self.message,
            span=self.span,
        )

    def __str__(self) -> str:
        """Formats the parse error with source location data.

        Returns:
            The formatted parse error string.
        """
        return (
            f"[{self.code}] {self.message} at index {self.span.start.index} "
            f"(line {self.span.start.line}, column {self.span.start.column})"
        )


class LexError(ParseError):
    """Raised when lexing fails."""

    code: ClassVar[str] = "lex_error"
