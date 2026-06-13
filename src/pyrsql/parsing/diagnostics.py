"""Structured parsing diagnostics."""

from __future__ import annotations

from pyrsql.core.source_issues import SourceDiagnostic


class ParseDiagnostic(SourceDiagnostic, frozen=True, gc=False, kw_only=True):
    """A structured parsing diagnostic."""
