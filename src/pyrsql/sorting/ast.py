"""AST nodes for pyrsql sort expressions."""

from dataclasses import dataclass
from enum import Enum

from pyrsql.selector.ast import Selector


class SortDirection(Enum):
    """Supported sort directions."""

    ASCENDING = "asc"
    DESCENDING = "desc"


@dataclass(frozen=True, slots=True)
class SortField:
    """Single parsed sort field."""

    selector: Selector
    direction: SortDirection
    ignore_case: bool
