"""Semantic sort nodes."""

from dataclasses import dataclass

from pyrsql.sorting.ast import SortDirection


@dataclass(frozen=True, slots=True)
class SemanticSortField:
    """Single sort field after selector normalization."""

    selector: str
    field_path: str
    direction: SortDirection
    ignore_case: bool
