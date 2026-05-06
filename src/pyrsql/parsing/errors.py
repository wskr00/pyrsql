"""Parsing error types."""

from typing import ClassVar
from dataclasses import dataclass

from pyrsql.parsing.source import SourceSpan
from pyrsql.parsing.diagnostics import ParseDiagnostic


@dataclass(frozen=True, slots=True)
class ParseError(ValueError):
    """Base exception for parsing failures."""

    message: str
    span: SourceSpan
    code: ClassVar[str] = "parse_error"

    @property
    def diagnostic(self) -> ParseDiagnostic:
        """Returns the structured diagnostic for this error."""
        return ParseDiagnostic(
            code=self.code,
            message=self.message,
            span=self.span,
        )

    def __str__(self) -> str:
        """Formats the parse error with source location data."""
        return str(self.diagnostic)


class LexError(ParseError):
    """Raised when lexing fails."""

    code: ClassVar[str] = "lex_error"
