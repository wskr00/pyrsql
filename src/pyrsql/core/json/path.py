"""Immutable JSON path primitives."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class JSONPath:
    """Represents a backend-neutral JSON path."""

    segments: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validates path segments."""
        if any(not segment for segment in self.segments):
            raise ValueError("JSON path segments cannot be empty.")

    @property
    def is_root(self) -> bool:
        """Returns whether the path targets the root JSON value."""
        return not self.segments

    def to_dot_path(self) -> str:
        """Returns the path as a dotted string."""
        return ".".join(self.segments)

