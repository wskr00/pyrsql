"""Source location models for parsing."""

import msgspec


class SourcePosition(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Represents a single position in the input source."""

    index: int
    line: int
    column: int

    def __post_init__(self) -> None:
        """Validates source position invariants.

        Raises:
            ValueError: If the position indices are invalid.
        """
        if self.index < 0:
            raise ValueError("Source position index cannot be negative.")
        if self.line <= 0:
            raise ValueError("Source position line must be greater than 0.")
        if self.column <= 0:
            raise ValueError("Source position column must be greater than 0.")


class SourceSpan(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Represents a half-open span in the input source."""

    start: SourcePosition
    end: SourcePosition

    def __post_init__(self) -> None:
        """Validates span ordering invariants.

        Raises:
            ValueError: If the span end precedes the start.
        """
        if self.end.index < self.start.index:
            raise ValueError("Source span end cannot precede start.")

    @classmethod
    def cover(cls, start: "SourceSpan", end: "SourceSpan") -> "SourceSpan":
        """Builds a span that covers two existing spans.

        Returns:
            A span covering the start of the first and end of the second span.
        """
        return cls(start=start.start, end=end.end)


class SourceText(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Wraps immutable source text and exposes helper methods."""

    text: str

    def __post_init__(self) -> None:
        """Validates the source text.

        Raises:
            TypeError: If the source text is not a string.
        """
        if not isinstance(self.text, str):
            raise TypeError("Source text must be a string.")

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
