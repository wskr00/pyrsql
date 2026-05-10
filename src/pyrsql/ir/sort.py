"""Bound logical sort nodes."""

from __future__ import annotations

import msgspec

from pyrsql.ir.query import BoundSelectorNode
from pyrsql.sorting.ast import SortDirection


class BoundSortField(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """A single bound sort field."""

    selector: BoundSelectorNode
    direction: SortDirection
    ignore_case: bool

    def __post_init__(self) -> None:
        """Validates bound sort field invariants.

        Raises:
            TypeError: If any field has the wrong runtime type.
        """
        if not isinstance(self.selector, BoundSelectorNode):
            raise TypeError(
                "Bound sort field selector must be a BoundSelectorNode.",
            )
        if not isinstance(self.direction, SortDirection):
            raise TypeError(
                "Bound sort field direction must be a SortDirection.",
            )
        if not isinstance(self.ignore_case, bool):
            raise TypeError("Bound sort field ignore_case must be a bool.")


class BoundSort(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """A bound sort request."""

    fields: tuple[BoundSortField, ...]

    def __post_init__(self) -> None:
        """Validates bound sort invariants.

        Raises:
            ValueError: If no bound sort fields are present.
        """
        if not self.fields:
            raise ValueError(
                "Bound sort must contain at least one bound sort field.",
            )
