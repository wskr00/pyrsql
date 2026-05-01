"""High-level query object."""

from dataclasses import dataclass

from pyrsql.backends.base import Backend
from pyrsql.core.compiler import CompilationResult
from pyrsql.core.options import QueryOptions


@dataclass(frozen=True, slots=True)
class Query:
    """Represents a backend-neutral parsed query request.

    The custom lexer, parser, and AST are still pending. For now, the query
    object preserves the raw text and project-wide options so the public API
    and backend contracts can evolve independently from parser internals.
    """

    text: str
    options: QueryOptions

    @classmethod
    def parse(
        cls,
        query_text: str,
        *,
        options: QueryOptions | None = None,
    ) -> "Query":
        """Creates a query object from raw RSQL text."""
        return cls(text=query_text, options=options or QueryOptions())

    def compile(self, *, backend: Backend) -> CompilationResult:
        """Compiles the query using the provided backend."""
        compiled_query = backend.compile_query(self)
        return CompilationResult(
            backend_name=backend.name,
            compiled_query=compiled_query,
        )
