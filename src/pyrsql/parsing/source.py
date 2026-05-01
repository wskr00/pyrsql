"""Source location models for parsing."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourcePosition:
    """Represents a single position in the input source."""

    index: int
    line: int
    column: int


@dataclass(frozen=True, slots=True)
class SourceSpan:
    """Represents a half-open span in the input source."""

    start: SourcePosition
    end: SourcePosition

    @classmethod
    def cover(cls, start: "SourceSpan", end: "SourceSpan") -> "SourceSpan":
        """Builds a span that covers two existing spans."""
        return cls(start=start.start, end=end.end)


@dataclass(frozen=True, slots=True)
class SourceText:
    """Wraps immutable source text and exposes helper methods."""

    text: str

    def __post_init__(self) -> None:
        """Validates the source text."""
        if not isinstance(self.text, str):
            raise TypeError("Source text must be a string.")

    @property
    def length(self) -> int:
        """Returns the source length."""
        return len(self.text)

    def slice(self, start: int, end: int) -> str:
        """Returns a substring by raw indices."""
        return self.text[start:end]
