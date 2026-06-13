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


class SourceText(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Wraps immutable source text and exposes helper methods."""

    text: str

    @property
    def length(self) -> int:
        """Returns the source length.

        Returns:
            The length of the wrapped source text.
        """
        return len(self.text)

    def slice(self, start: int, end: int) -> str:
        """Returns a substring by raw indices.

        Returns:
            The sliced substring.
        """
        return self.text[start:end]
