"""High-level query object."""

from dataclasses import dataclass
from typing import Any

from pyrsql.backends.base import Backend
from pyrsql.core.compiler import CompilationResult
from pyrsql.core.options import QueryOptions
from pyrsql.parsing.ast import Expression
from pyrsql.parsing.parser import Parser
from pyrsql.semantic.analyzer import SemanticAnalyzer
from pyrsql.semantic.ast import SemanticExpression


@dataclass(frozen=True, slots=True)
class Query:
    """Represents a backend-neutral parsed query request.

    The query preserves the raw text, the parsed expression tree, and the
    backend-neutral semantic representation used by later compilation steps.
    """

    text: str
    options: QueryOptions
    expression: Expression | None = None
    semantic_expression: SemanticExpression | None = None

    @classmethod
    def parse(
        cls,
        query_text: str,
        *,
        options: QueryOptions | None = None,
    ) -> "Query":
        """Creates a query object from raw RSQL text."""
        resolved_options = options or QueryOptions()
        expression = cls.parse_expression(query_text, options=resolved_options)
        semantic_expression = cls.analyze_expression(
            expression,
            options=resolved_options,
        )
        return cls(
            text=query_text,
            options=resolved_options,
            expression=expression,
            semantic_expression=semantic_expression,
        )

    @staticmethod
    def parse_expression(
        query_text: str,
        *,
        options: QueryOptions,
    ) -> Expression:
        """Parses raw query text into a syntax tree."""
        return Parser(
            query_text,
            limits=options.parse_limits,
            operator_registry=options.operator_registry,
        ).parse()

    @staticmethod
    def analyze_expression(
        expression: Expression,
        *,
        options: QueryOptions,
    ) -> SemanticExpression:
        """Analyzes a syntax tree into a semantic expression."""
        return SemanticAnalyzer(options).analyze(expression)

    def compile(self, *, backend: Backend) -> CompilationResult:
        """Compiles the query using the provided backend."""
        compiled_query = backend.compile_query(self)
        return CompilationResult(
            backend_name=backend.name,
            compiled_query=compiled_query,
        )

    def apply(
        self,
        target: Any,
        model: type[Any],
        *,
        backend: Backend,
    ) -> Any:
        """Compiles and applies the query using the provided backend."""
        return self.compile(backend=backend).apply(target=target, model=model)
