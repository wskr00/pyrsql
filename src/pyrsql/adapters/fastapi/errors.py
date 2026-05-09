"""FastAPI adapter error helpers."""

import msgspec

from pyrsql.parsing.errors import ParseError
from pyrsql.semantic.errors import (
    FieldBlacklistedError,
    FieldNotWhitelistedError,
    FunctionBlacklistedError,
    FunctionNotWhitelistedError,
    SemanticError,
)
from pyrsql.sorting.errors import (
    SortFieldBlacklistedError,
    SortFieldNotWhitelistedError,
    SortFunctionBlacklistedError,
    SortFunctionNotWhitelistedError,
    SortParseError,
)


class FastAPIAdapterErrorPayload(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
):
    """Structured adapter error payload for HTTP translation.

    Attributes:
        parameter: Name of the query parameter associated with the failure.
        error_type: Stable machine-readable error category.
        message: Human-readable error message.
    """

    parameter: str
    error_type: str
    message: str
    details: tuple["FastAPIAdapterErrorDetail", ...]


class FastAPIAdapterErrorDetail(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
):
    """Structured detail item exposed in FastAPI adapter responses."""

    code: str
    message: str
    field: str | None = None


def _extract_field_from_message(message: str) -> str | None:
    """Extracts a quoted field path from a normalized pyrsql message."""
    quote_start = message.find("'")
    if quote_start < 0:
        return None
    quote_end = message.find("'", quote_start + 1)
    if quote_end < 0:
        return None
    field = message[quote_start + 1 : quote_end]
    return field or None


def build_query_error_payload(
    parameter_name: str,
    error: ParseError | SemanticError,
) -> FastAPIAdapterErrorPayload:
    """Builds a payload for a filter/query parsing or semantic failure.

    Args:
        parameter_name: Query parameter name associated with the failure.
        error: Parsing or semantic error raised by pyrsql.

    Returns:
        A normalized FastAPI error payload.
    """
    error_type = "query_parse_error"
    detail_code = getattr(error, "code", "query_parse_error")
    detail_field = None
    if isinstance(error, SemanticError):
        error_type = "query_semantic_error"
        if isinstance(
            error,
            (
                FieldNotWhitelistedError,
                FieldBlacklistedError,
                FunctionNotWhitelistedError,
                FunctionBlacklistedError,
            ),
        ):
            detail_field = _extract_field_from_message(error.message)
    return FastAPIAdapterErrorPayload(
        parameter=parameter_name,
        error_type=error_type,
        message=str(error),
        details=(
            FastAPIAdapterErrorDetail(
                code=detail_code,
                message=error.message,
                field=detail_field,
            ),
        ),
    )


def build_sort_error_payload(
    parameter_name: str,
    error: Exception,
) -> FastAPIAdapterErrorPayload:
    """Builds a payload for a sort parsing or semantic failure.

    Args:
        parameter_name: Query parameter name associated with the failure.
        error: Sorting error raised by pyrsql.

    Returns:
        A normalized FastAPI error payload.
    """
    error_type = "sort_error"
    detail_code = getattr(error, "code", "sort_error")
    detail_field = None
    if isinstance(error, SortParseError):
        error_type = "sort_parse_error"
    elif isinstance(
        error,
        (
            SortFieldNotWhitelistedError,
            SortFieldBlacklistedError,
            SortFunctionNotWhitelistedError,
            SortFunctionBlacklistedError,
        ),
    ):
        error_type = "sort_semantic_error"
        detail_field = _extract_field_from_message(str(error))
    return FastAPIAdapterErrorPayload(
        parameter=parameter_name,
        error_type=error_type,
        message=str(error),
        details=(
            FastAPIAdapterErrorDetail(
                code=detail_code,
                message=getattr(error, "message", str(error)),
                field=detail_field,
            ),
        ),
    )


def build_page_error_payload(
    parameter_name: str,
    *,
    error_type: str,
    message: str,
) -> FastAPIAdapterErrorPayload:
    """Builds a payload for page-related adapter validation failures.

    Args:
        parameter_name: Query parameter name associated with the failure.
        error_type: Machine-readable error category.
        message: Human-readable error message.

    Returns:
        A normalized FastAPI error payload.
    """
    return FastAPIAdapterErrorPayload(
        parameter=parameter_name,
        error_type=error_type,
        message=message,
        details=(
            FastAPIAdapterErrorDetail(
                code=error_type,
                message=message,
            ),
        ),
    )
