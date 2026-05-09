"""High-level query object."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pyrsql.core.compiler import CompilationResult
from pyrsql.core.options import QueryOptions
from pyrsql.parsing.parser import Parser
from pyrsql.semantic.binder import SemanticBinder

if TYPE_CHECKING:
    from pyrsql.ir.query import BoundComparison, BoundLogical
    from pyrsql.orms.base import ORM
    from pyrsql.parsing.ast import Expression

_DEFAULT_QUERY_OPTIONS = QueryOptions()


def _resolve_query_options(
    options: QueryOptions | None,
) -> QueryOptions:
    """Returns the provided options or the shared immutable default.

    Returns:
        The provided options, or the shared default when omitted.
    """
    return options or _DEFAULT_QUERY_OPTIONS


def _parse_query_expression(
    query_text: str,
    *,
    options: QueryOptions,
) -> Expression:
    """Parses raw query text into a syntax tree.

    Returns:
        The parsed query expression tree.
    """
    return Parser(
        query_text,
        limits=options.parse_limits,
        operator_registry=options.operator_registry,
    ).parse()


def _bind_query_expression(
    expression: Expression,
    *,
    options: QueryOptions,
) -> BoundComparison | BoundLogical:
    """Binds a syntax tree into logical query IR.

    Returns:
        The bound logical query IR.
    """
    return SemanticBinder(options).bind(expression)


@dataclass(frozen=True, slots=True)
class Query:
    """Represents a parsed ORM-neutral query request.

    The query preserves the raw text, the parsed expression tree, and the
    bound logical representation used by later compilation stages.

    Attributes:
        text: Raw RSQL text that produced the query.
        options: Normalized query configuration used during parsing.
        expression: Parsed syntax tree, if parsing succeeded.
        bound_expression: Bound logical expression tree.
    """

    text: str
    options: QueryOptions
    expression: Expression
    bound_expression: BoundComparison | BoundLogical

    @classmethod
    def parse(
        cls,
        query_text: str,
        *,
        options: QueryOptions | None = None,
    ) -> Query:
        """Parses raw RSQL text into a query object.

        Args:
            query_text: Raw RSQL text to parse.
            options: Optional query configuration.

        Returns:
            A parsed query object.
        """
        resolved_options = _resolve_query_options(options)
        expression = cls.parse_expression(query_text, options=resolved_options)
        bound_expression = cls.bind_expression(
            expression,
            options=resolved_options,
        )
        return cls(
            text=query_text,
            options=resolved_options,
            expression=expression,
            bound_expression=bound_expression,
        )

    @staticmethod
    def parse_expression(
        query_text: str,
        *,
        options: QueryOptions,
    ) -> Expression:
        """Parses raw RSQL text into a syntax tree.

        Args:
            query_text: Raw RSQL text to parse.
            options: Query configuration used by the parser.

        Returns:
            The parsed syntax tree.
        """
        return _parse_query_expression(query_text, options=options)

    @staticmethod
    def bind_expression(
        expression: Expression,
        *,
        options: QueryOptions,
    ) -> BoundComparison | BoundLogical:
        """Binds a syntax tree into logical query IR.

        Args:
            expression: Parsed syntax tree to bind.
            options: Query configuration used by semantic binding.

        Returns:
            The bound logical query IR.
        """
        return _bind_query_expression(expression, options=options)

    def compile(self, *, orm: ORM) -> CompilationResult:
        """Compiles the query using the provided ORM.

        Args:
            orm: ORM adapter used to compile the query.

        Returns:
            The ORM-specific compilation result.
        """
        compiled_query = orm.compile_query(self)
        return CompilationResult(
            orm_name=orm.name,
            compiled_query=compiled_query,
        )

    def apply(
        self,
        target: Any,
        model: type[Any],
        *,
        orm: ORM,
    ) -> Any:
        """Compiles and applies the query using the provided ORM.

        Args:
            target: ORM-specific target to mutate.
            model: ORM model class used to resolve the query.
            orm: ORM adapter used to compile the query.

        Returns:
            The value returned by the ORM-specific apply operation.
        """
        return self.compile(orm=orm).apply(target=target, model=model)
