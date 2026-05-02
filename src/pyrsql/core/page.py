"""ORM-neutral pagination request objects."""

from dataclasses import dataclass
from typing import Any

from pyrsql.core.compiler import PageCompilationResult
from pyrsql.orms.base import ORM


@dataclass(frozen=True, slots=True)
class PageRequest:
    """Represents an ORM-neutral pagination request."""

    page_number: int
    page_size: int

    def __post_init__(self) -> None:
        """Validates pagination invariants."""
        if self.page_number < 0:
            raise ValueError("page_number must be greater than or equal to 0.")
        if self.page_size <= 0:
            raise ValueError("page_size must be greater than 0.")

    @classmethod
    def of(
        cls,
        page_number: int,
        page_size: int,
    ) -> "PageRequest":
        """Builds a pagination request from page number and page size."""
        return cls(page_number=page_number, page_size=page_size)

    @classmethod
    def from_offset(
        cls,
        *,
        offset: int,
        limit: int,
    ) -> "PageRequest":
        """Builds a pagination request from offset and limit."""
        if offset < 0:
            raise ValueError("offset must be greater than or equal to 0.")
        if limit <= 0:
            raise ValueError("limit must be greater than 0.")
        page_number, remainder = divmod(offset, limit)
        if remainder != 0:
            raise ValueError(
                "offset must align with limit to convert into a PageRequest."
            )
        return cls(page_number=page_number, page_size=limit)

    @property
    def offset(self) -> int:
        """Returns the zero-based row offset for this request."""
        return self.page_number * self.page_size

    @property
    def limit(self) -> int:
        """Returns the maximum number of rows for this request."""
        return self.page_size

    def compile(self, *, orm: ORM) -> PageCompilationResult:
        """Compiles the page request using the provided orm."""
        compiled_page = orm.compile_page_request(self)
        return PageCompilationResult(
            orm_name=orm.name,
            compiled_page=compiled_page,
        )

    def apply(
        self,
        target: Any,
        model: type[Any],
        *,
        orm: ORM,
    ) -> Any:
        """Compiles and applies the page request using the orm."""
        return self.compile(orm=orm).apply(target=target, model=model)
