"""AST nodes for pyrsql sort expressions."""

from enum import Enum

import msgspec

from pyrsql.selector.ast import SelectorNode


class SortDirection(Enum):
    """Supported sort directions."""

    ASCENDING = "asc"
    DESCENDING = "desc"

    @classmethod
    def from_raw(cls, raw_direction: str) -> "SortDirection | None":
        """Matches a raw token to a supported sort direction.

        Args:
            raw_direction: Raw direction token from the sort expression.

        Returns:
            The matching direction, or None when the token is unsupported.
        """
        match raw_direction.lower():
            case "asc":
                return cls.ASCENDING
            case "desc":
                return cls.DESCENDING
            case _:
                return None


class SortField(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Single parsed sort field.

    Attributes:
        selector: Selector node to sort by.
        direction: Sort direction to apply.
        ignore_case: Whether case should be ignored when sorting.
    """

    selector: SelectorNode
    direction: SortDirection
    ignore_case: bool

    def __post_init__(self) -> None:
        """Validates sort field invariants."""
        if not isinstance(self.selector, SelectorNode):
            raise TypeError("Sort field selector must be a SelectorNode.")
        if not isinstance(self.direction, SortDirection):
            raise TypeError("Sort field direction must be a SortDirection.")
        if not isinstance(self.ignore_case, bool):
            raise TypeError("Sort field ignore_case must be a bool.")
