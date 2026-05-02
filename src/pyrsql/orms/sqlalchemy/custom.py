"""Custom predicate extension points for the SQLAlchemy orm."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.sql.elements import ColumnElement

from pyrsql.core.options import QueryOptions


@dataclass(frozen=True, slots=True)
class SQLAlchemyCustomPredicateInput:
    """Structured input for ORM-specific custom predicate builders."""

    expression: ColumnElement[Any]
    python_type: type[Any] | None
    values: tuple[Any, ...]
    options: QueryOptions


SQLAlchemyCustomPredicate = Callable[
    [SQLAlchemyCustomPredicateInput],
    ColumnElement[bool],
]
