"""Immutable JSON path primitives."""

import json
import re

import msgspec

_SIMPLE_JSONPATH_SEGMENT_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class JSONPath(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Represents an ORM-neutral JSON path.

    Attributes:
        segments: Ordered path segments from the JSON root to the target.
    """

    segments: tuple[str, ...] = ()
    _dot_path: str = ""
    _postgresql_jsonpath: str = "$"

    def __post_init__(self) -> None:
        """Validates path segments.

        Raises:
            ValueError: If any segment is empty.
        """
        for segment in self.segments:
            if not segment:
                raise ValueError("JSON path segments cannot be empty.")
            if segment != segment.strip():
                raise ValueError(
                    "JSON path segments must not contain outer whitespace."
                )
        object.__setattr__(self, "_dot_path", ".".join(self.segments))
        object.__setattr__(
            self,
            "_postgresql_jsonpath",
            self._build_postgresql_jsonpath(),
        )

    @property
    def is_root(self) -> bool:
        """Whether the path targets the root JSON value."""
        return not self.segments

    def to_dot_path(self) -> str:
        """The path rendered as a dotted string."""
        return self._dot_path

    def to_postgresql_jsonpath(self) -> str:
        """The path rendered as a PostgreSQL jsonpath root expression."""
        return self._postgresql_jsonpath

    def _build_postgresql_jsonpath(self) -> str:
        """Builds one PostgreSQL jsonpath root expression."""
        if self.is_root:
            return "$"
        return "$" + "".join(
            self._render_postgresql_segment(segment)
            for segment in self.segments
        )

    @staticmethod
    def _render_postgresql_segment(segment: str) -> str:
        """Builds one PostgreSQL jsonpath segment."""
        if _SIMPLE_JSONPATH_SEGMENT_PATTERN.fullmatch(segment) is not None:
            return f".{segment}"
        return "." + json.dumps(segment)
