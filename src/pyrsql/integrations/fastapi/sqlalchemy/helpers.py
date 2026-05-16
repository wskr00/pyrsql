"""Shared helpers for FastAPI + SQLAlchemy integrations."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from fastapi import HTTPException
import msgspec
from sqlalchemy import func, select

from pyrsql.adapters.fastapi import RequestCriteria
from pyrsql.adapters.fastapi.errors import (
    FastAPIAdapterErrorDetail,
    FastAPIAdapterErrorPayload,
)
from pyrsql.orms.sqlalchemy.errors import SQLAlchemyORMError

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import NoReturn

    from pyrsql.adapters.fastapi import FastAPICriteriaConfig
    from pyrsql.orms.sqlalchemy import SQLAlchemyORM
    from pyrsql.orms.sqlalchemy.types import SQLAlchemyModel, SQLAlchemySelect


def _extract_field_from_message(message: str) -> str | None:
    """Extracts a quoted field path from backend error messages.

    Returns:
        The extracted field path, or ``None`` when no quoted field exists.
    """
    quote_start = message.find("'")
    if quote_start < 0:
        return None
    quote_end = message.find("'", quote_start + 1)
    if quote_end < 0:
        return None
    field = message[quote_start + 1 : quote_end]
    return field or None


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
    payload = FastAPIAdapterErrorPayload(
        parameter=parameter_name,
        error_type=error_type,
        details=(
            FastAPIAdapterErrorDetail(
                code=error_type,
                message=str(error),
                field=_extract_field_from_message(str(error)),
            ),
        ),
    )
    raise HTTPException(
        status_code=422,
        detail={
            "parameter": payload.parameter,
            "type": payload.error_type,
            "errors": msgspec.to_builtins(payload.details),
        },
    )


def raise_query_backend_http_error(
    config: "FastAPICriteriaConfig",  # noqa: UP037
    error: SQLAlchemyORMError,
) -> NoReturn:
    """Raises one normalized HTTP 422 query error for backend failures."""
    _raise_backend_http_error(
        parameter_name=config.filter_parameter,
        error_type="query_backend_error",
        error=error,
    )


def raise_sort_backend_http_error(
    config: "FastAPICriteriaConfig",  # noqa: UP037
    error: SQLAlchemyORMError,
) -> NoReturn:
    """Raises one normalized HTTP 422 sort error for backend failures."""
    _raise_backend_http_error(
        parameter_name=config.sort_parameter,
        error_type="sort_backend_error",
        error=error,
    )


@contextmanager
def query_backend_http_errors(
    config: "FastAPICriteriaConfig",  # noqa: UP037
) -> Iterator[None]:
    """Translates backend query failures into normalized HTTP 422 errors."""
    try:
        yield
    except SQLAlchemyORMError as error:
        raise_query_backend_http_error(config, error)


@contextmanager
def sort_backend_http_errors(
    config: "FastAPICriteriaConfig",  # noqa: UP037
) -> Iterator[None]:
    """Translates backend sort failures into normalized HTTP 422 errors."""
    try:
        yield
    except SQLAlchemyORMError as error:
        raise_sort_backend_http_error(config, error)


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
