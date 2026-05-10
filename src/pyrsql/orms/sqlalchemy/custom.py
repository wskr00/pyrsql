"""Custom predicate extension points for the SQLAlchemy orm."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import msgspec
from sqlalchemy.sql.elements import ColumnElement

if TYPE_CHECKING:
    from pyrsql.core.options import QueryOptions


class SQLAlchemyCustomPredicateInput(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
):
    """Structured input for ORM-specific custom predicate builders."""

    expression: ColumnElement[Any]
    python_type: type[Any] | None
    values: tuple[Any, ...]
    options: QueryOptions


SQLAlchemyCustomPredicate = Callable[
    [SQLAlchemyCustomPredicateInput],
    ColumnElement[bool],
]
