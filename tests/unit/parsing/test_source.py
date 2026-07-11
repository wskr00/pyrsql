"""Unit tests for parsing source location helpers."""

from __future__ import annotations

from pyrsql.parsing.source import SourcePosition, SourceSpan


def test_source_span_cover_uses_outer_boundaries() -> None:
    """Source span cover uses the first start and last end positions."""
    start = SourceSpan(
        start=SourcePosition(index=0, line=1, column=1),
        end=SourcePosition(index=4, line=1, column=5),
    )
    end = SourceSpan(
        start=SourcePosition(index=5, line=1, column=6),
        end=SourcePosition(index=9, line=1, column=10),
    )

    covered = SourceSpan.cover(start, end)

    assert covered.start == start.start
    assert covered.end == end.end
