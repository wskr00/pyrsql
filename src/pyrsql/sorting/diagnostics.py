"""Structured sorting diagnostics."""

import msgspec


class SortDiagnostic(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """A structured sorting diagnostic."""

    code: str
    message: str

    def __str__(self) -> str:
        """Formats the diagnostic as a stable string."""
        return f"[{self.code}] {self.message}"
