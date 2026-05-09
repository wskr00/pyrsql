"""Compiled query support for SQLAlchemy."""

import msgspec

from pyrsql.core.options import QueryOptions
from pyrsql.ir.query import BoundComparison, BoundLogical
from pyrsql.orms.sqlalchemy.statement import (
    apply_relationship_joins,
    require_sqlalchemy_select,
)
from pyrsql.orms.sqlalchemy.translator import SQLAlchemyExpressionTranslator
from pyrsql.orms.sqlalchemy.types import SQLAlchemyModel, SQLAlchemySelect


class SQLAlchemyCompiledQuery(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
):
    """Compiled SQLAlchemy query plan.

    Attributes:
        expression: Bound query IR to lower into SQLAlchemy clauses.
        options: Query configuration used during translation.
        translator: Translator responsible for producing SQLAlchemy objects.
    """

    expression: BoundComparison | BoundLogical
    options: QueryOptions
    translator: SQLAlchemyExpressionTranslator

    def apply(
        self,
        target: SQLAlchemySelect | object,
        model: SQLAlchemyModel,
    ) -> SQLAlchemySelect:
        """Applies the compiled query to a SQLAlchemy Select.

        Args:
            target: SQLAlchemy select statement to mutate.
            model: SQLAlchemy mapped class used to resolve fields.

        Returns:
            A SQLAlchemy select with filters and joins applied.
        """
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
