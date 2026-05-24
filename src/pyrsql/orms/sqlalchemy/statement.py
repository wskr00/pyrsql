"""Helpers for mutating SQLAlchemy Select statements."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from sqlalchemy.sql import Select

from pyrsql.core.joins import JoinHint
from pyrsql.orms.sqlalchemy.errors import SQLAlchemyORMError

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pyrsql.orms.sqlalchemy.types import (
        SQLAlchemyJoinPlan,
        SQLAlchemySelect,
    )

_EMPTY_JOIN_HINTS = MappingProxyType({})


def require_sqlalchemy_select(target: object) -> SQLAlchemySelect:
    """Validates and narrows an ORM target to a SQLAlchemy Select.

    Returns:
        The validated SQLAlchemy ``Select`` object.

    Raises:
        TypeError: If the target is not a SQLAlchemy ``Select``.
    """
    if not isinstance(target, Select):
        raise TypeError("SQLAlchemy ORM expects a sqlalchemy.sql.Select.")
    return target


def apply_relationship_joins(
    statement: SQLAlchemySelect,
    joins: tuple[SQLAlchemyJoinPlan, ...],
    *,
    join_hints: Mapping[str, JoinHint] | None = None,
) -> SQLAlchemySelect:
    """Applies relationship joins once each while preserving order.

    Returns:
        The statement with the requested joins applied.

    """
    if not joins:
        return statement
    join_hints = join_hints if join_hints is not None else _EMPTY_JOIN_HINTS
    deduplicated_joins = joins if len(joins) == 1 else dict.fromkeys(joins)
    updated_statement = statement
    for join_plan in deduplicated_joins:
        updated_statement = _apply_join_plan(
            updated_statement,
            join_plan,
            join_hints=join_hints,
        )
    return updated_statement


def _apply_join_plan(
    statement: SQLAlchemySelect,
    join_plan: SQLAlchemyJoinPlan,
    *,
    join_hints: Mapping[str, JoinHint],
) -> SQLAlchemySelect:
    """Applies one relationship join according to the resolved join hint.

    Returns:
        The statement with one join applied.

    Raises:
        SQLAlchemyORMError: If a join hint requests an unsupported join type.
    """
    resolved_hint = join_hints.get(join_plan.key, join_plan.default_hint)
    if resolved_hint is JoinHint.INNER:
        return statement.join(join_plan.attribute)
    if resolved_hint is JoinHint.LEFT:
        return statement.outerjoin(join_plan.attribute)
    raise SQLAlchemyORMError(
        "SQLAlchemy ORM does not support RIGHT joins via join_hints.",
    )
