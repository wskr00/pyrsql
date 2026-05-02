"""Source location models for parsing."""

from dataclasses import dataclass
from dataclasses import field


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
    _length: int = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Validates the source text."""
        if not isinstance(self.text, str):
            raise TypeError("Source text must be a string.")
        object.__setattr__(self, "_length", len(self.text))

    @property
    def length(self) -> int:
        """Returns the source length."""
        return self._length

    def slice(self, start: int, end: int) -> str:
        """Returns a substring by raw indices."""
        return self.text[start:end]
