"""Helpers for mutating SQLAlchemy Select statements."""

from collections.abc import Mapping

from sqlalchemy.sql import Select

from pyrsql.core.joins import JoinHint
from pyrsql.orms.sqlalchemy.errors import SQLAlchemyORMError
from pyrsql.orms.sqlalchemy.types import SQLAlchemyJoinPlan, SQLAlchemySelect


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

    Raises:
        SQLAlchemyORMError: If a join hint requests an unsupported join type.
    """
    join_hints = join_hints or {}
    deduplicated_joins = dict.fromkeys(joins)
    updated_statement = statement
    for join_plan in deduplicated_joins:
        resolved_hint = join_hints.get(join_plan.key, join_plan.default_hint)
        if resolved_hint is JoinHint.INNER:
            updated_statement = updated_statement.join(join_plan.attribute)
            continue
        if resolved_hint is JoinHint.LEFT:
            updated_statement = updated_statement.outerjoin(join_plan.attribute)
            continue
        raise SQLAlchemyORMError(
            "SQLAlchemy ORM does not support RIGHT joins via join_hints.",
        )
    return updated_statement
