"""Backend-neutral compilation result objects."""

from dataclasses import dataclass
from typing import Any

from pyrsql.backends.base import CompiledPageRequest
from pyrsql.backends.base import CompiledQuery
from pyrsql.backends.base import CompiledSort


@dataclass(frozen=True, slots=True)
class CompilationResult:
    """Wraps a backend-specific compiled query object."""

    backend_name: str
    compiled_query: CompiledQuery

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies the compiled query to a backend-specific target."""
        return self.compiled_query.apply(target=target, model=model)


@dataclass(frozen=True, slots=True)
class SortCompilationResult:
    """Wraps a backend-specific compiled sort object."""

    backend_name: str
    compiled_sort: CompiledSort

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies the compiled sort to a backend-specific target."""
        return self.compiled_sort.apply(target=target, model=model)


@dataclass(frozen=True, slots=True)
class PageCompilationResult:
    """Wraps a backend-specific compiled page request object."""

    backend_name: str
    compiled_page: CompiledPageRequest

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies the compiled page request to a backend-specific target."""
        return self.compiled_page.apply(target=target, model=model)
