"""Semantic sort nodes."""

from dataclasses import dataclass

from pyrsql.selector.semantic import SemanticSelector
from pyrsql.sorting.ast import SortDirection


@dataclass(frozen=True, slots=True)
class SemanticSortField:
    """Single sort field after selector normalization."""

    selector: SemanticSelector
    direction: SortDirection
    ignore_case: bool
