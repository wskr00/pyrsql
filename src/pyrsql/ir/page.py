"""Bound logical pagination nodes."""

import msgspec


class BoundPage(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """A backend-independent pagination request."""

    page_number: int
    page_size: int

    def __post_init__(self) -> None:
        """Validates pagination invariants."""
        if self.page_number < 0:
            raise ValueError("page_number must be greater than or equal to 0.")
        if self.page_size <= 0:
            raise ValueError("page_size must be greater than 0.")

    @property
    def offset(self) -> int:
        """Returns the zero-based row offset."""
        return self.page_number * self.page_size

    @property
    def limit(self) -> int:
        """Returns the maximum number of rows."""
        return self.page_size
