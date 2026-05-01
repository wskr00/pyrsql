"""High-level query object."""

from dataclasses import dataclass

from pyrsql.backends.base import Backend
from pyrsql.core.compiler import CompilationResult
from pyrsql.core.options import QueryOptions
from pyrsql.parsing.ast import Node
from pyrsql.parsing.parser import Parser


@dataclass(frozen=True, slots=True)
class Query:
    """Represents a backend-neutral parsed query request.

    The custom lexer, parser, and AST are still pending. For now, the query
    object preserves the raw text and project-wide options so the public API
    and backend contracts can evolve independently from parser internals.
    """

    text: str
    options: QueryOptions
    expression: Node | None = None

    @classmethod
    def parse(
        cls,
        query_text: str,
        *,
        options: QueryOptions | None = None,
    ) -> "Query":
        """Creates a query object from raw RSQL text."""
        resolved_options = options or QueryOptions()
        expression = Parser(
            query_text,
            limits=resolved_options.parse_limits,
        ).parse()
        return cls(
            text=query_text,
            options=resolved_options,
            expression=expression,
        )

    def compile(self, *, backend: Backend) -> CompilationResult:
        """Compiles the query using the provided backend."""
        compiled_query = backend.compile_query(self)
        return CompilationResult(
            backend_name=backend.name,
            compiled_query=compiled_query,
        )
