"""Semantic analysis exceptions."""

from __future__ import annotations

from typing import ClassVar

from pyrsql.core.source_issues import SourceError
from pyrsql.semantic.diagnostics import SemanticDiagnostic


class SemanticError(SourceError):
    """Base exception for semantic analysis failures."""

    code: ClassVar[str] = "semantic_error"
    diagnostic_type: ClassVar[type[SemanticDiagnostic]] = SemanticDiagnostic


class FieldNotWhitelistedError(SemanticError):
    """Raised when a selector is not allowed by the whitelist."""

    code: ClassVar[str] = "field_not_whitelisted"


class FieldBlacklistedError(SemanticError):
    """Raised when a selector is blocked by the blacklist."""

    code: ClassVar[str] = "field_blacklisted"


class FunctionNotWhitelistedError(SemanticError):
    """Raised when a function selector is not allowed by the whitelist."""

    code: ClassVar[str] = "function_not_whitelisted"


class FunctionBlacklistedError(SemanticError):
    """Raised when a function selector is blocked by the blacklist."""

    code: ClassVar[str] = "function_blacklisted"
