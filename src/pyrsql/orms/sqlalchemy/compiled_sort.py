"""Compiled sort support for SQLAlchemy."""

import msgspec

from pyrsql.core.options import SortOptions
from pyrsql.ir.sort import BoundSort
from pyrsql.orms.sqlalchemy.sorter import SQLAlchemySortTranslator
from pyrsql.orms.sqlalchemy.statement import (
    apply_relationship_joins,
    require_sqlalchemy_select,
)
from pyrsql.orms.sqlalchemy.types import SQLAlchemyModel, SQLAlchemySelect


class SQLAlchemyCompiledSort(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
):
    """Compiled SQLAlchemy sort plan.

    Attributes:
        sort_plan: Bound sort IR to lower into order clauses.
        options: Sort configuration used during translation.
        translator: Translator responsible for producing SQLAlchemy objects.
    """

    sort_plan: BoundSort | None
    options: SortOptions
    translator: SQLAlchemySortTranslator

    def apply(
        self,
        target: SQLAlchemySelect | object,
        model: SQLAlchemyModel,
    ) -> SQLAlchemySelect:
        """Applies the compiled sort to a SQLAlchemy Select.

        Args:
            target: SQLAlchemy select statement to mutate.
            model: SQLAlchemy mapped class used to resolve fields.

        Returns:
            A SQLAlchemy select with joins and ordering applied.
        """
        statement = require_sqlalchemy_select(target)
        if self.sort_plan is None:
            return statement
        joins, order_clauses = self.translator.translate(
            model,
            self.sort_plan,
            options=self.options,
        )
        statement = apply_relationship_joins(
            statement,
            joins,
            join_hints=self.options.join_hints,
        )
        if not order_clauses:
            return statement
        return statement.order_by(*order_clauses)
