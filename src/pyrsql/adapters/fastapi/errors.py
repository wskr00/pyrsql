"""FastAPI adapter error helpers."""

from dataclasses import dataclass

from pyrsql.parsing.errors import ParseError
from pyrsql.semantic.errors import SemanticError
from pyrsql.sorting.errors import (
    SortFieldBlacklistedError,
    SortFieldNotWhitelistedError,
    SortFunctionBlacklistedError,
    SortFunctionNotWhitelistedError,
    SortParseError,
)


@dataclass(frozen=True, slots=True)
class FastAPIAdapterErrorPayload:
    """Structured adapter error payload for HTTP translation."""

    parameter: str
    error_type: str
    message: str


def build_query_error_payload(
    parameter_name: str,
    error: ParseError | SemanticError,
) -> FastAPIAdapterErrorPayload:
    """Builds a payload for a filter/query parsing or semantic failure."""
    error_type = "query_parse_error"
    if isinstance(error, SemanticError):
        error_type = "query_semantic_error"
    return FastAPIAdapterErrorPayload(
        parameter=parameter_name,
        error_type=error_type,
        message=str(error),
    )


def build_sort_error_payload(
    parameter_name: str,
    error: Exception,
) -> FastAPIAdapterErrorPayload:
    """Builds a payload for a sort parsing or semantic failure."""
    error_type = "sort_error"
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
    return FastAPIAdapterErrorPayload(
        parameter=parameter_name,
        error_type=error_type,
        message=str(error),
    )


def build_page_error_payload(
    parameter_name: str,
    *,
    error_type: str,
    message: str,
) -> FastAPIAdapterErrorPayload:
    """Builds a payload for page-related adapter validation failures."""
    return FastAPIAdapterErrorPayload(
        parameter=parameter_name,
        error_type=error_type,
        message=message,
    )
