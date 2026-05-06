"""Semantic analysis exceptions."""

from typing import ClassVar

from dataclasses import dataclass

from pyrsql.parsing.source import SourceSpan
from pyrsql.semantic.diagnostics import SemanticDiagnostic


@dataclass(frozen=True, slots=True)
class SemanticError(ValueError):
    """Base exception for semantic analysis failures."""

    message: str
    span: SourceSpan
    code: ClassVar[str] = "semantic_error"

    @property
    def diagnostic(self) -> SemanticDiagnostic:
        """Returns the structured diagnostic for this error."""
        return SemanticDiagnostic(
            code=self.code,
            message=self.message,
            span=self.span,
        )

    def __str__(self) -> str:
        """Formats semantic errors with source position data."""
        return str(self.diagnostic)


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
