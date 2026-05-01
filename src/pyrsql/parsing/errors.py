"""Parsing error types."""

from dataclasses import dataclass

from pyrsql.parsing.source import SourceSpan


@dataclass(frozen=True, slots=True)
class ParseError(ValueError):
    """Base exception for parsing failures."""

    message: str
    span: SourceSpan

    def __str__(self) -> str:
        """Formats the parse error with source location data."""
        return (
            f"{self.message} at index {self.span.start.index} "
            f"(line {self.span.start.line}, column {self.span.start.column})"
        )


@dataclass(frozen=True, slots=True)
class LexError(ParseError):
    """Raised when lexing fails."""
