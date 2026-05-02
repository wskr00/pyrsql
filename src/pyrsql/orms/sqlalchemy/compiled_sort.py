"""Compiled sort support for SQLAlchemy."""

from dataclasses import dataclass
from typing import Any

from sqlalchemy.sql import Select

from pyrsql.core.options import SortOptions
from pyrsql.orms.sqlalchemy.sorter import SQLAlchemySortTranslator
from pyrsql.orms.sqlalchemy.statement import apply_relationship_joins
from pyrsql.sorting.semantic import SemanticSortField


@dataclass(frozen=True, slots=True)
class SQLAlchemyCompiledSort:
    """Compiled SQLAlchemy sort plan."""

    fields: tuple[SemanticSortField, ...]
    options: SortOptions
    translator: SQLAlchemySortTranslator

    def apply(self, target: Any, model: type[Any]) -> Any:
        """Applies the compiled sort to a SQLAlchemy Select."""
        if not isinstance(target, Select):
            raise TypeError("SQLAlchemy ORM expects a sqlalchemy.sql.Select.")
        joins, order_clauses = self.translator.translate(
            model,
            self.fields,
            options=self.options,
        )
        statement = apply_relationship_joins(
            target,
            joins,
            join_hints=self.options.join_hints,
        )
        if not order_clauses:
            return statement
        return statement.order_by(*order_clauses)
