"""Bound logical pagination nodes."""

import msgspec


class BoundPage(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """A backend-independent pagination request."""

    page_number: int
    page_size: int

    @property
    def offset(self) -> int:
        """Returns the zero-based row offset.

        Returns:
            The zero-based row offset.
        """
        return self.page_number * self.page_size

    @property
    def limit(self) -> int:
        """Returns the maximum number of rows.

        Returns:
            The maximum number of rows.
        """
        return self.page_size
