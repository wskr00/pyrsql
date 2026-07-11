"""Source location models for parsing."""

from __future__ import annotations

import msgspec


class SourcePosition(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Represents a single position in the input source."""

    index: int
    line: int
    column: int


class SourceSpan(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Represents a half-open span in the input source."""

    start: SourcePosition
    end: SourcePosition

    @classmethod
    def cover(cls, start: SourceSpan, end: SourceSpan) -> SourceSpan:
        """Builds a span that covers two existing spans.

        Returns:
            A span covering the start of the first and end of the second span.
        """
        return cls(start=start.start, end=end.end)
