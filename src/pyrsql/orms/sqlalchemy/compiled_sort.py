"""Compiled sort support for SQLAlchemy."""

from dataclasses import dataclass

from pyrsql.core.options import SortOptions
from pyrsql.orms.sqlalchemy.sorter import SQLAlchemySortTranslator
from pyrsql.orms.sqlalchemy.statement import (
    apply_relationship_joins,
    require_sqlalchemy_select,
)
from pyrsql.orms.sqlalchemy.types import SQLAlchemyModel, SQLAlchemySelect
from pyrsql.sorting.semantic import SemanticSortField


@dataclass(frozen=True, slots=True)
class SQLAlchemyCompiledSort:
    """Compiled SQLAlchemy sort plan."""

    fields: tuple[SemanticSortField, ...]
    options: SortOptions
    translator: SQLAlchemySortTranslator

    def apply(
        self,
        target: SQLAlchemySelect | object,
        model: SQLAlchemyModel,
    ) -> SQLAlchemySelect:
        """Applies the compiled sort to a SQLAlchemy Select."""
        statement = require_sqlalchemy_select(target)
        joins, order_clauses = self.translator.translate(
            model,
            self.fields,
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
