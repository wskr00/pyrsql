"""Backend-neutral compilation result objects."""

from dataclasses import dataclass
from typing import Any

from pyrsql.backends.base import CompiledQuery


@dataclass(frozen=True, slots=True)
class CompilationResult:
    """Wraps a backend-specific compiled query object."""

    backend_name: str
    compiled_query: CompiledQuery

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies the compiled query to a backend-specific target."""
        return self.compiled_query.apply(target=target, model=model)
