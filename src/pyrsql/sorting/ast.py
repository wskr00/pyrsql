"""AST nodes for pyrsql sort expressions."""

from dataclasses import dataclass
from enum import Enum

from pyrsql.selector.ast import Selector


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


@dataclass(frozen=True, slots=True)
class SortField:
    """Single parsed sort field.

    Attributes:
        selector: Selector to sort by.
        direction: Sort direction to apply.
        ignore_case: Whether case should be ignored when sorting.
    """

    selector: Selector
    direction: SortDirection
    ignore_case: bool
