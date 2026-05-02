"""ORM-neutral compilation result objects."""

from dataclasses import dataclass
from typing import Any

from pyrsql.orms.base import CompiledPageRequest
from pyrsql.orms.base import CompiledQuery
from pyrsql.orms.base import CompiledSort


@dataclass(frozen=True, slots=True)
class CompilationResult:
    """Wraps a ORM-specific compiled query object."""

    orm_name: str
    compiled_query: CompiledQuery

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies the compiled query to a ORM-specific target."""
        return self.compiled_query.apply(target=target, model=model)


@dataclass(frozen=True, slots=True)
class SortCompilationResult:
    """Wraps a ORM-specific compiled sort object."""

    orm_name: str
    compiled_sort: CompiledSort

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies the compiled sort to a ORM-specific target."""
        return self.compiled_sort.apply(target=target, model=model)


@dataclass(frozen=True, slots=True)
class PageCompilationResult:
    """Wraps a ORM-specific compiled page request object."""

    orm_name: str
    compiled_page: CompiledPageRequest

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies the compiled page request to a ORM-specific target."""
        return self.compiled_page.apply(target=target, model=model)
