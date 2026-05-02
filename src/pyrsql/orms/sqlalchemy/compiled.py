"""Compiled query support for SQLAlchemy."""

from dataclasses import dataclass
from typing import Any

from sqlalchemy.sql import Select

from pyrsql.orms.sqlalchemy.translator import SQLAlchemyExpressionTranslator
from pyrsql.orms.sqlalchemy.statement import apply_relationship_joins
from pyrsql.core.options import QueryOptions
from pyrsql.semantic.ast import SemanticExpression


@dataclass(frozen=True, slots=True)
class SQLAlchemyCompiledQuery:
    """Compiled SQLAlchemy query plan."""

    expression: SemanticExpression
    options: QueryOptions
    translator: SQLAlchemyExpressionTranslator

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies the compiled query to a SQLAlchemy Select."""
        if not isinstance(target, Select):
            raise TypeError(
                "SQLAlchemy ORM expects a sqlalchemy.sql.Select."
            )
        joins, predicate = self.translator.translate(
            model,
            self.expression,
            options=self.options,
        )
        statement = apply_relationship_joins(
            target,
            joins,
            join_hints=self.options.join_hints,
        )
        if self.options.distinct:
            statement = statement.distinct()
        return statement.where(predicate)
