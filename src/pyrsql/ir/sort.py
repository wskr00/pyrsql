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


class BoundSort(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """A bound sort request."""

    fields: tuple[BoundSortField, ...]
