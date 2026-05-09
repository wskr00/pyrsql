"""Security and complexity limits for sort parsing."""

import msgspec


class SortLimits(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Configurable limits for sort parsing."""

    max_sort_length: int = 4096
    max_fields: int = 32
    max_field_path_length: int = 256

    def __post_init__(self) -> None:
        """Validates sort parser limit invariants."""
        if self.max_sort_length <= 0:
            raise ValueError("max_sort_length must be greater than 0.")
        if self.max_fields <= 0:
            raise ValueError("max_fields must be greater than 0.")
        if self.max_field_path_length <= 0:
            raise ValueError("max_field_path_length must be greater than 0.")


DEFAULT_SORT_LIMITS = SortLimits()
