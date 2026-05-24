"""Security and complexity limits for sort parsing."""

from __future__ import annotations

import msgspec

from pyrsql._validation import validate_positive_int


class SortLimits(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Configurable limits for sort parsing."""

    max_sort_length: int = 4096
    max_fields: int = 32
    max_field_path_length: int = 256

    def __post_init__(self) -> None:
        """Validates sort parser limit invariants."""
        validate_positive_int(
            self.max_sort_length,
            field_name="max_sort_length",
        )
        validate_positive_int(
            self.max_fields,
            field_name="max_fields",
        )
        validate_positive_int(
            self.max_field_path_length,
            field_name="max_field_path_length",
        )


DEFAULT_SORT_LIMITS = SortLimits()
