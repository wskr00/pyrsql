"""Helpers for mutating SQLAlchemy Select statements."""

from typing import Any, Mapping

from sqlalchemy.sql import Select

from pyrsql.core.joins import JoinHint
from pyrsql.orms.sqlalchemy.errors import SQLAlchemyORMError
from pyrsql.orms.sqlalchemy.types import SQLAlchemyJoinPlan


def apply_relationship_joins(
    statement: Select[Any],
    joins: tuple[SQLAlchemyJoinPlan, ...],
    *,
    join_hints: Mapping[str, JoinHint] | None = None,
) -> Select[Any]:
    """Applies relationship joins once each while preserving order."""
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
            "SQLAlchemy ORM does not support RIGHT joins via join_hints."
        )
    return updated_statement
