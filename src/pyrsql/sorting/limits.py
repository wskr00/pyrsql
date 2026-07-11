"""Security and complexity limits for sort parsing."""

from __future__ import annotations

import msgspec


class SortLimits(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Configurable limits for sort parsing."""

    max_sort_length: int = 4096
    max_fields: int = 32
    max_field_path_length: int = 256


DEFAULT_SORT_LIMITS = SortLimits()
