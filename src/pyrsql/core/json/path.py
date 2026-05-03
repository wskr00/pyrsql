"""Immutable JSON path primitives."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class JSONPath:
    """Represents an ORM-neutral JSON path.

    Attributes:
        segments: Ordered path segments from the JSON root to the target.
    """

    segments: tuple[str, ...] = ()
    _dot_path: str = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Validates path segments.

        Raises:
            ValueError: If any segment is empty.
        """
        for segment in self.segments:
            if not segment:
                raise ValueError("JSON path segments cannot be empty.")
        object.__setattr__(self, "_dot_path", ".".join(self.segments))

    @property
    def is_root(self) -> bool:
        """Whether the path targets the root JSON value."""
        return not self.segments

    def to_dot_path(self) -> str:
        """The path rendered as a dotted string."""
        return self._dot_path
