"""High-level query object."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

import msgspec

from pyrsql.core.compiler import CompilationResult
from pyrsql.core.options import QueryOptions
from pyrsql.parsing.parser import Parser
from pyrsql.semantic.binder import SemanticBinder

if TYPE_CHECKING:
    from pyrsql.orms.base import ORM
    from pyrsql.parsing.ast import Expression

_TargetT = TypeVar("_TargetT")
_ModelT = TypeVar("_ModelT")

_DEFAULT_QUERY_OPTIONS = QueryOptions()


class Query(msgspec.Struct, frozen=True, gc=False):
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
    bound_expression: Expression

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
        resolved_options = (
            _DEFAULT_QUERY_OPTIONS if options is None else options
        )
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
        return Parser(
            query_text,
            limits=options.parse_limits,
            operator_registry=options.operator_registry,
        ).parse()

    @staticmethod
    def bind_expression(
        expression: Expression,
        *,
        options: QueryOptions,
    ) -> Expression:
        """Binds a syntax tree into logical query IR.

        Args:
            expression: Parsed syntax tree to bind.
            options: Query configuration used by semantic binding.

        Returns:
            The semantically validated expression tree.
        """
        return SemanticBinder(options).bind(expression)

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
            compiled=compiled_query,
        )

    def apply(
        self,
        target: _TargetT,
        model: type[_ModelT],
        *,
        orm: ORM,
    ) -> _TargetT:
        """Compiles and applies the query using the provided ORM.

        Args:
            target: ORM-specific target to mutate.
            model: ORM model class used to resolve the query.
            orm: ORM adapter used to compile the query.

        Returns:
            The value returned by the ORM-specific apply operation.
        """
        return orm.compile_query(self).apply(target=target, model=model)
