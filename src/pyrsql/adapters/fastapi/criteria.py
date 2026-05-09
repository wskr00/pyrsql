"""FastAPI request criteria objects."""

from typing import Any

import msgspec

from pyrsql.core.page import PageRequest
from pyrsql.core.query import Query
from pyrsql.core.sort import Sort
from pyrsql.orms.base import ORM


class RequestCriteria(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
):
    """Represents request-derived pyrsql criteria for a FastAPI endpoint."""

    query: Query | None = None
    sort: Sort | None = None
    page_request: PageRequest | None = None

    def __post_init__(self) -> None:
        """Validates criteria payload types.

        Raises:
            TypeError: If any provided criterion has the wrong runtime type.
        """
        if self.query is not None and not isinstance(self.query, Query):
            raise TypeError("query must be a Query instance or None.")
        if self.sort is not None and not isinstance(self.sort, Sort):
            raise TypeError("sort must be a Sort instance or None.")
        if self.page_request is not None and not isinstance(
            self.page_request,
            PageRequest,
        ):
            raise TypeError(
                "page_request must be a PageRequest instance or None.",
            )

    @property
    def is_empty(self) -> bool:
        """Indicates whether no query components are present.

        Returns:
            ``True`` when query, sort, and page criteria are all absent.
        """
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
        """Applies the criteria to an ORM-specific target.

        Returns:
            The transformed ORM-specific target after applying all criteria.
        """
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
