"""Compiled query support for SQLAlchemy."""

from __future__ import annotations

from typing import TYPE_CHECKING

import msgspec

from pyrsql.orms.sqlalchemy.statement import (
    apply_relationship_joins,
    require_sqlalchemy_select,
)

if TYPE_CHECKING:
    from pyrsql.core.options import QueryOptions
    from pyrsql.orms.sqlalchemy.translator import SQLAlchemyExpressionTranslator
    from pyrsql.orms.sqlalchemy.types import SQLAlchemyModel, SQLAlchemySelect
    from pyrsql.parsing.ast import Expression


class SQLAlchemyCompiledQuery(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
):
    """Compiled SQLAlchemy query plan.

    Attributes:
        expression: Semantically validated query expression to lower.
        options: Query configuration used during translation.
        translator: Translator responsible for producing SQLAlchemy objects.
    """

    expression: Expression
    options: QueryOptions
    translator: SQLAlchemyExpressionTranslator

    def apply(
        self,
        target: SQLAlchemySelect,
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
