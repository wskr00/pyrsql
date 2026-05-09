"""Shared helpers for FastAPI + SQLAlchemy integrations."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from sqlalchemy import func, select

from pyrsql.adapters.fastapi import RequestCriteria

if TYPE_CHECKING:
    from pyrsql.orms.sqlalchemy import SQLAlchemyORM
    from pyrsql.orms.sqlalchemy.types import SQLAlchemyModel, SQLAlchemySelect


def require_request_criteria(criteria: RequestCriteria) -> RequestCriteria:
    """Validates and returns request criteria objects.

    Returns:
        The validated request criteria instance.

    Raises:
        TypeError: If the provided value is not a ``RequestCriteria``.
    """
    if not isinstance(criteria, RequestCriteria):
        raise TypeError("criteria must be a RequestCriteria.")
    return criteria


def apply_query_with_orm(
    statement: SQLAlchemySelect,
    model: SQLAlchemyModel,
    criteria: RequestCriteria,
    orm: SQLAlchemyORM,
) -> SQLAlchemySelect:
    """Applies only query/filter semantics using the configured ORM.

    Returns:
        A statement with only filter semantics applied.
    """
    if criteria.query is None:
        return statement
    return cast(
        "SQLAlchemySelect",
        criteria.query.apply(statement, model, orm=orm),
    )


def apply_sort_and_page_with_orm(
    statement: SQLAlchemySelect,
    model: SQLAlchemyModel,
    criteria: RequestCriteria,
    orm: SQLAlchemyORM,
) -> SQLAlchemySelect:
    """Applies sort and page semantics using the configured ORM.

    Returns:
        A statement with sort and page semantics applied.
    """
    updated_statement = statement
    if criteria.sort is not None:
        updated_statement = cast(
            "SQLAlchemySelect",
            criteria.sort.apply(updated_statement, model, orm=orm),
        )
    if criteria.page_request is not None:
        updated_statement = cast(
            "SQLAlchemySelect",
            criteria.page_request.apply(updated_statement, model, orm=orm),
        )
    return updated_statement


def count_from_filtered_select(
    filtered_statement: SQLAlchemySelect,
) -> SQLAlchemySelect:
    """Builds a count statement from an already-filtered select.

    Returns:
        A count statement derived from the filtered select.
    """
    return select(func.count()).select_from(  # pylint: disable=not-callable
        filtered_statement.order_by(None).subquery(),
    )
