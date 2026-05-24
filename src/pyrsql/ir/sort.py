"""Bound logical sort nodes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import msgspec

if TYPE_CHECKING:
    from pyrsql.ir.query import BoundSelectorNode
    from pyrsql.sorting.ast import SortDirection


class BoundSortField(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """A single bound sort field."""

    selector: BoundSelectorNode
    direction: SortDirection
    ignore_case: bool


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
