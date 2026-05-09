"""Structured parsing diagnostics."""

import msgspec

from pyrsql.parsing.source import SourceSpan


class ParseDiagnostic(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """A structured parsing diagnostic."""

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
