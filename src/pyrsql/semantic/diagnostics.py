"""Structured semantic diagnostics."""

from __future__ import annotations

from pyrsql.core.source_issues import SourceDiagnostic


class SemanticDiagnostic(SourceDiagnostic, frozen=True, gc=False, kw_only=True):
    """A structured semantic diagnostic."""
