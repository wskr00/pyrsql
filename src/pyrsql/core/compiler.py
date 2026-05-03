"""ORM-neutral compilation result objects."""

from dataclasses import dataclass
from typing import Any

from pyrsql.orms.base import CompiledPageRequest, CompiledQuery, CompiledSort


@dataclass(frozen=True, slots=True)
class CompilationResult:
    """Wraps an ORM-specific compiled query object.

    Attributes:
        orm_name: Name of the ORM used to produce the compilation.
        compiled_query: ORM-specific compiled query payload.
    """

    orm_name: str
    compiled_query: CompiledQuery

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies the compiled query to an ORM-specific target.

        Args:
            target: ORM-specific target to mutate.
            model: ORM model class used to resolve the query.

        Returns:
            The value returned by the compiled query application.
        """
        return self.compiled_query.apply(target=target, model=model)


@dataclass(frozen=True, slots=True)
class SortCompilationResult:
    """Wraps an ORM-specific compiled sort object.

    Attributes:
        orm_name: Name of the ORM used to produce the compilation.
        compiled_sort: ORM-specific compiled sort payload.
    """

    orm_name: str
    compiled_sort: CompiledSort

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies the compiled sort to an ORM-specific target.

        Args:
            target: ORM-specific target to mutate.
            model: ORM model class used to resolve the sort.

        Returns:
            The value returned by the compiled sort application.
        """
        return self.compiled_sort.apply(target=target, model=model)


@dataclass(frozen=True, slots=True)
class PageCompilationResult:
    """Wraps an ORM-specific compiled page request object.

    Attributes:
        orm_name: Name of the ORM used to produce the compilation.
        compiled_page: ORM-specific compiled page payload.
    """

    orm_name: str
    compiled_page: CompiledPageRequest

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies the compiled page request to an ORM-specific target.

        Args:
            target: ORM-specific target to mutate.
            model: ORM model class used to resolve the page request.

        Returns:
            The value returned by the compiled page application.
        """
        return self.compiled_page.apply(target=target, model=model)
