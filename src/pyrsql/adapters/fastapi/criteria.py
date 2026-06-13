"""FastAPI request criteria objects."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

import msgspec

if TYPE_CHECKING:
    from pyrsql.core.page import PageRequest
    from pyrsql.core.query import Query
    from pyrsql.core.sort import Sort
    from pyrsql.orms.base import ORM

_TargetT = TypeVar("_TargetT")
_ModelT = TypeVar("_ModelT")


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
        target: _TargetT,
        model: type[_ModelT],
        *,
        orm: ORM,
    ) -> _TargetT:
        """Applies the criteria to an ORM-specific target.

        Returns:
            The transformed ORM-specific target after applying all criteria.
        """
        if self.is_empty:
            return target
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
