"""Compiled query support for SQLAlchemy."""

from dataclasses import dataclass

from pyrsql.core.options import QueryOptions
from pyrsql.orms.sqlalchemy.statement import (
    apply_relationship_joins,
    require_sqlalchemy_select,
)
from pyrsql.orms.sqlalchemy.translator import SQLAlchemyExpressionTranslator
from pyrsql.orms.sqlalchemy.types import SQLAlchemyModel, SQLAlchemySelect
from pyrsql.semantic.ast import SemanticExpression


@dataclass(frozen=True, slots=True)
class SQLAlchemyCompiledQuery:
    """Compiled SQLAlchemy query plan."""

    expression: SemanticExpression
    options: QueryOptions
    translator: SQLAlchemyExpressionTranslator

    def apply(
        self,
        target: SQLAlchemySelect | object,
        model: SQLAlchemyModel,
    ) -> SQLAlchemySelect:
        """Applies the compiled query to a SQLAlchemy Select."""
        statement = require_sqlalchemy_select(target)
        joins, predicate = self.translator.translate(
            model,
            self.expression,
            options=self.options,
        )
        statement = apply_relationship_joins(
            statement,
            joins,
            join_hints=self.options.join_hints,
        )
        if self.options.distinct:
            statement = statement.distinct()
        return statement.where(predicate)
