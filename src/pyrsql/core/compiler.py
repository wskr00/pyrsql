"""ORM-neutral compilation result objects."""

from typing import Any

import msgspec

from pyrsql.orms.base import CompiledPageRequest, CompiledQuery, CompiledSort


class CompilationResult(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Wraps an ORM-specific compiled query object.

    Attributes:
        orm_name: Name of the ORM used to produce the compilation.
        compiled_query: ORM-specific compiled query payload.
    """

    orm_name: str
    compiled_query: CompiledQuery

    def __post_init__(self) -> None:
        """Validates compilation result invariants."""
        if not self.orm_name:
            raise ValueError("Compilation result orm_name cannot be empty.")

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies the compiled query to an ORM-specific target.

        Args:
            target: ORM-specific target to mutate.
            model: ORM model class used to resolve the query.

        Returns:
            The value returned by the compiled query application.
        """
        return self.compiled_query.apply(target=target, model=model)


class SortCompilationResult(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
):
    """Wraps an ORM-specific compiled sort object.

    Attributes:
        orm_name: Name of the ORM used to produce the compilation.
        compiled_sort: ORM-specific compiled sort payload.
    """

    orm_name: str
    compiled_sort: CompiledSort

    def __post_init__(self) -> None:
        """Validates sort compilation result invariants."""
        if not self.orm_name:
            raise ValueError(
                "Sort compilation result orm_name cannot be empty."
            )

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies the compiled sort to an ORM-specific target.

        Args:
            target: ORM-specific target to mutate.
            model: ORM model class used to resolve the sort.

        Returns:
            The value returned by the compiled sort application.
        """
        return self.compiled_sort.apply(target=target, model=model)


class PageCompilationResult(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
):
    """Wraps an ORM-specific compiled page request object.

    Attributes:
        orm_name: Name of the ORM used to produce the compilation.
        compiled_page: ORM-specific compiled page payload.
    """

    orm_name: str
    compiled_page: CompiledPageRequest

    def __post_init__(self) -> None:
        """Validates page compilation result invariants."""
        if not self.orm_name:
            raise ValueError(
                "Page compilation result orm_name cannot be empty."
            )

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies the compiled page request to an ORM-specific target.

        Args:
            target: ORM-specific target to mutate.
            model: ORM model class used to resolve the page request.

        Returns:
            The value returned by the compiled page application.
        """
        return self.compiled_page.apply(target=target, model=model)
