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
        """Returns the matching direction for a raw token, if supported."""
        match raw_direction.lower():
            case "asc":
                return cls.ASCENDING
            case "desc":
                return cls.DESCENDING
            case _:
                return None


@dataclass(frozen=True, slots=True)
class SortField:
    """Single parsed sort field."""

    selector: Selector
    direction: SortDirection
    ignore_case: bool
