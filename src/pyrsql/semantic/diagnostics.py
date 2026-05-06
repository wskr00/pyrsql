"""Structured semantic diagnostics."""

import msgspec

# TODO(restructuring): semantic diagnostics still reuse parsing spans. Replace
# this once parsing stabilizes its final source range types for the compiler
# pipeline.
from pyrsql.parsing.source import SourceSpan


class SemanticDiagnostic(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """A structured semantic diagnostic."""

    code: str
    message: str
    span: SourceSpan

    def __str__(self) -> str:
        """Formats the diagnostic with source position data."""
        return (
            f"[{self.code}] {self.message} at index {self.span.start.index} "
            f"(line {self.span.start.line}, column {self.span.start.column})"
        )
