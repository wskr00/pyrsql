"""Security and complexity limits for sort parsing."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SortLimits:
    """Configurable limits for sort parsing."""

    max_sort_length: int = 4096
    max_fields: int = 32
    max_field_path_length: int = 256
