"""Semantic analysis exceptions."""

from dataclasses import dataclass

from pyrsql.parsing.source import SourceSpan


@dataclass(frozen=True, slots=True)
class SemanticError(ValueError):
    """Base exception for semantic analysis failures."""

    message: str
    span: SourceSpan

    def __str__(self) -> str:
        """Formats semantic errors with source position data."""
        return (
            f"{self.message} at index {self.span.start.index} "
            f"(line {self.span.start.line}, column {self.span.start.column})"
        )


@dataclass(frozen=True, slots=True)
class FieldNotWhitelistedError(SemanticError):
    """Raised when a selector is not allowed by the whitelist."""


@dataclass(frozen=True, slots=True)
class FieldBlacklistedError(SemanticError):
    """Raised when a selector is blocked by the blacklist."""
