"""Semantic analysis exceptions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from pyrsql.semantic.diagnostics import SemanticDiagnostic

if TYPE_CHECKING:
    from pyrsql.parsing.source import SourceSpan


@dataclass(frozen=True, slots=True)
class SemanticError(ValueError):
    """Base exception for semantic analysis failures."""

    message: str
    span: SourceSpan
    code: ClassVar[str] = "semantic_error"

    @property
    def diagnostic(self) -> SemanticDiagnostic:
        """Returns the structured diagnostic for this error.

        Returns:
            The structured semantic diagnostic.
        """
        return SemanticDiagnostic(
            code=self.code,
            message=self.message,
            span=self.span,
        )

    def __str__(self) -> str:
        """Formats semantic errors with source position data.

        Returns:
            The formatted semantic error string.
        """
        return (
            f"[{self.code}] {self.message} at index {self.span.start.index} "
            f"(line {self.span.start.line}, column {self.span.start.column})"
        )


@dataclass(frozen=True, slots=True)
class FieldNotWhitelistedError(SemanticError):
    """Raised when a selector is not allowed by the whitelist."""

    code: ClassVar[str] = "field_not_whitelisted"


@dataclass(frozen=True, slots=True)
class FieldBlacklistedError(SemanticError):
    """Raised when a selector is blocked by the blacklist."""

    code: ClassVar[str] = "field_blacklisted"


@dataclass(frozen=True, slots=True)
class FunctionNotWhitelistedError(SemanticError):
    """Raised when a function selector is not allowed by the whitelist."""

    code: ClassVar[str] = "function_not_whitelisted"


@dataclass(frozen=True, slots=True)
class FunctionBlacklistedError(SemanticError):
    """Raised when a function selector is blocked by the blacklist."""

    code: ClassVar[str] = "function_blacklisted"
