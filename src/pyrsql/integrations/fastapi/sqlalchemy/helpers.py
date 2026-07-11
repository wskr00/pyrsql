"""Shared helpers for FastAPI + SQLAlchemy integrations."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from fastapi import HTTPException
from sqlalchemy import func, select

from pyrsql.adapters.fastapi.errors import FastAPIAdapterErrorPayload
from pyrsql.integrations.fastapi.sqlalchemy.payloads import (
    SQLAlchemyPaginatedSelect,
)
from pyrsql.orms.sqlalchemy.errors import SQLAlchemyORMError

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import NoReturn

    from pyrsql.adapters.fastapi import (
        FastAPICriteriaConfig,
        RequestCriteria,
    )
    from pyrsql.orms.sqlalchemy import SQLAlchemyORM
    from pyrsql.orms.sqlalchemy.types import SQLAlchemyModel, SQLAlchemySelect


def _raise_backend_http_error(
    *,
    parameter_name: str,
    error_type: str,
    error: SQLAlchemyORMError,
) -> NoReturn:
    """Raises one normalized HTTP 422 error for backend integration failures.

    Raises:
        HTTPException: Always raised with a normalized error payload.
    """
    payload = FastAPIAdapterErrorPayload.from_backend_error(
        parameter_name,
        error_type=error_type,
        error=error,
    )
    raise HTTPException(
        status_code=payload.status_code,
        detail=payload.to_http_detail(),
    )


@contextmanager
def query_backend_http_errors(
    config: "FastAPICriteriaConfig",  # noqa: UP037
) -> Iterator[None]:
    """Translates backend query failures into normalized HTTP 422 errors."""
    try:
        yield
    except SQLAlchemyORMError as error:
        _raise_backend_http_error(
            parameter_name=config.filter_parameter,
            error_type="query_backend_error",
            error=error,
        )


@contextmanager
def sort_backend_http_errors(
    config: "FastAPICriteriaConfig",  # noqa: UP037
) -> Iterator[None]:
    """Translates backend sort failures into normalized HTTP 422 errors."""
    try:
        yield
    except SQLAlchemyORMError as error:
        _raise_backend_http_error(
            parameter_name=config.sort_parameter,
            error_type="sort_backend_error",
            error=error,
        )


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
    return criteria.query.apply(statement, model, orm=orm)


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
        updated_statement = criteria.sort.apply(
            updated_statement,
            model,
            orm=orm,
        )
    if criteria.page_request is not None:
        updated_statement = criteria.page_request.apply(
            updated_statement,
            model,
            orm=orm,
        )
    return updated_statement


def count_from_filtered_select(
    filtered_statement: SQLAlchemySelect,
) -> SQLAlchemySelect:
    """Builds a count statement from an already-filtered select.

    Returns:
        A count statement derived from the filtered select.
    """
    return select(func.count()).select_from(
        filtered_statement.order_by(None).subquery(),
    )


def build_paginated_select(
    *,
    statement: SQLAlchemySelect,
    filtered_statement: SQLAlchemySelect,
) -> SQLAlchemyPaginatedSelect:
    """Builds the shared list/count payload for paginated query flows.

    Returns:
        The paired list and count SQLAlchemy statements.
    """
    return SQLAlchemyPaginatedSelect(
        statement=statement,
        count_statement=count_from_filtered_select(filtered_statement),
    )
