"""Parsing error types."""

from __future__ import annotations

from typing import ClassVar

from pyrsql.core.source_issues import SourceError


class ParseError(SourceError):
    """Base exception for parsing failures."""

    code: ClassVar[str] = "parse_error"


class LexError(ParseError):
    """Raised when lexing fails."""

    code: ClassVar[str] = "lex_error"
