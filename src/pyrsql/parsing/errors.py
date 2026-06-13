"""Parsing error types."""

from __future__ import annotations

from typing import ClassVar

from pyrsql.core.source_issues import SourceError
from pyrsql.parsing.diagnostics import ParseDiagnostic


class ParseError(SourceError):
    """Base exception for parsing failures."""

    code: ClassVar[str] = "parse_error"
    diagnostic_type: ClassVar[type[ParseDiagnostic]] = ParseDiagnostic


class LexError(ParseError):
    """Raised when lexing fails."""

    code: ClassVar[str] = "lex_error"
