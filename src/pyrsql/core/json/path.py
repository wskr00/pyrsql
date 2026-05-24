"""Immutable JSON path primitives."""

from __future__ import annotations

import re

import msgspec

_SIMPLE_JSONPATH_SEGMENT_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_JSON_ENCODER = msgspec.json.Encoder()


class JSONPath(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Represents an ORM-neutral JSON path.

    Attributes:
        segments: Ordered path segments from the JSON root to the target.
    """

    segments: tuple[str, ...] = ()
    _dot_path: str = ""
    _postgresql_jsonpath: str = "$"

    def __post_init__(self) -> None:
        """Materializes derived cached path representations."""
        normalized_segments = tuple(self.segments)
        msgspec.structs.force_setattr(
            self,
            "segments",
            normalized_segments,
        )
        msgspec.structs.force_setattr(
            self,
            "_dot_path",
            ".".join(normalized_segments),
        )
        msgspec.structs.force_setattr(
            self,
            "_postgresql_jsonpath",
            self._build_postgresql_jsonpath(normalized_segments),
        )

    @property
    def is_root(self) -> bool:
        """Whether the path targets the root JSON value.

        Returns:
            ``True`` when the path has no segments.
        """
        return not self.segments

    def to_dot_path(self) -> str:
        """The path rendered as a dotted string.

        Returns:
            The cached dotted representation of the JSON path.
        """
        return self._dot_path

    def to_postgresql_jsonpath(self) -> str:
        """The path rendered as a PostgreSQL jsonpath root expression.

        Returns:
            The cached PostgreSQL ``jsonpath`` representation.
        """
        return self._postgresql_jsonpath

    def _build_postgresql_jsonpath(
        self,
        segments: tuple[str, ...],
    ) -> str:
        """Builds one PostgreSQL jsonpath root expression.

        Returns:
            A PostgreSQL ``jsonpath`` string rooted at ``$``.
        """
        if not segments:
            return "$"
        return "$" + "".join(
            self._render_postgresql_segment(segment) for segment in segments
        )

    @staticmethod
    def _render_postgresql_segment(segment: str) -> str:
        """Builds one PostgreSQL jsonpath segment.

        Returns:
            One rendered PostgreSQL ``jsonpath`` segment.
        """
        if _SIMPLE_JSONPATH_SEGMENT_PATTERN.fullmatch(segment) is not None:
            return f".{segment}"
        return "." + _JSON_ENCODER.encode(segment).decode()
