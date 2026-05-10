"""ORM-neutral pagination request objects."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

import msgspec

from pyrsql.core.compiler import PageCompilationResult
from pyrsql.ir.page import BoundPage

if TYPE_CHECKING:
    from pyrsql.orms.base import ORM

_TargetT = TypeVar("_TargetT")
_ModelT = TypeVar("_ModelT")


class PageRequest(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Represents an ORM-neutral pagination request.

    Attributes:
        page_number: Zero-based page number.
        page_size: Number of rows requested per page.
    """

    page_number: int
    page_size: int

    def __post_init__(self) -> None:
        """Validates pagination invariants.

        Raises:
            ValueError: If the page number is negative or the page size is not
                positive.
        """
        if self.page_number < 0:
            raise ValueError("page_number must be greater than or equal to 0.")
        if self.page_size <= 0:
            raise ValueError("page_size must be greater than 0.")

    @classmethod
    def of(
        cls,
        page_number: int,
        page_size: int,
    ) -> PageRequest:
        """Builds a pagination request from page number and page size.

        Args:
            page_number: Zero-based page number.
            page_size: Number of rows requested per page.

        Returns:
            A validated pagination request.
        """
        return cls(page_number=page_number, page_size=page_size)

    @classmethod
    def from_offset(
        cls,
        *,
        offset: int,
        limit: int,
    ) -> PageRequest:
        """Builds a pagination request from offset and limit.

        Args:
            offset: Zero-based row offset.
            limit: Maximum number of rows requested.

        Returns:
            A validated pagination request.

        Raises:
            ValueError: If the offset or limit is invalid, or if the offset
                does not align with the limit.
        """
        if offset < 0:
            raise ValueError("offset must be greater than or equal to 0.")
        if limit <= 0:
            raise ValueError("limit must be greater than 0.")
        page_number, remainder = divmod(offset, limit)
        if remainder != 0:
            raise ValueError(
                "offset must align with limit to convert into a PageRequest.",
            )
        return cls(page_number=page_number, page_size=limit)

    @property
    def offset(self) -> int:
        """The zero-based row offset for this request.

        Returns:
            The zero-based row offset.
        """
        return self.page_number * self.page_size

    @property
    def limit(self) -> int:
        """The maximum number of rows for this request.

        Returns:
            The maximum number of rows to fetch.
        """
        return self.page_size

    @property
    def bound_page(self) -> BoundPage:
        """The logical pagination IR for this request.

        Returns:
            The bound pagination IR for this request.
        """
        return BoundPage(
            page_number=self.page_number,
            page_size=self.page_size,
        )

    def compile(self, *, orm: ORM) -> PageCompilationResult:
        """Compiles the page request using the provided ORM.

        Args:
            orm: ORM adapter used to compile the page request.

        Returns:
            The ORM-specific page compilation result.
        """
        compiled_page = orm.compile_page_request(self)
        return PageCompilationResult(
            orm_name=orm.name,
            compiled_page=compiled_page,
        )

    def apply(
        self,
        target: _TargetT,
        model: type[_ModelT],
        *,
        orm: ORM,
    ) -> _TargetT:
        """Compiles and applies the page request using the ORM.

        Args:
            target: ORM-specific target to mutate.
            model: ORM model class used to resolve the page request.
            orm: ORM adapter used to compile the page request.

        Returns:
            The value returned by the ORM-specific apply operation.
        """
        return self.compile(orm=orm).apply(target=target, model=model)
