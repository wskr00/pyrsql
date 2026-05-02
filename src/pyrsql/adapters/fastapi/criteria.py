"""FastAPI request criteria objects."""

from dataclasses import dataclass
from typing import Any

from pyrsql.core.page import PageRequest
from pyrsql.core.query import Query
from pyrsql.core.sort import Sort
from pyrsql.orms.base import ORM


@dataclass(frozen=True, slots=True)
class RequestCriteria:
    """Represents request-derived pyrsql criteria for a FastAPI endpoint."""

    query: Query | None = None
    sort: Sort | None = None
    page_request: PageRequest | None = None

    @property
    def is_empty(self) -> bool:
        """Indicates whether no query components are present."""
        return (
            self.query is None
            and self.sort is None
            and self.page_request is None
        )

    def apply(
        self,
        target: Any,
        model: type[Any],
        *,
        orm: ORM,
    ) -> Any:
        """Applies the criteria to an ORM-specific target."""
        current_target = target
        if self.query is not None:
            current_target = self.query.apply(
                current_target,
                model,
                orm=orm,
            )
        if self.sort is not None:
            current_target = self.sort.apply(
                current_target,
                model,
                orm=orm,
            )
        if self.page_request is not None:
            current_target = self.page_request.apply(
                current_target,
                model,
                orm=orm,
            )
        return current_target
