"""FastAPI adapter error helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from pyrsql.orms import ORMError
    from pyrsql.parsing.source import SourceSpan

    SortAdapterError = (
        SortParseError
        | SortFieldNotWhitelistedError
        | SortFieldBlacklistedError
        | SortFunctionNotWhitelistedError
        | SortFunctionBlacklistedError
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
        error_type: Stable machine-readable problem category.
    """

    parameter: str
    error_type: str
    details: tuple[FastAPIAdapterErrorDetail, ...]

    @classmethod
    def _single_detail_payload(
        cls,
        *,
        parameter_name: str,
        error_type: str,
        code: str,
        detail: str,
        field: str | None = None,
        location: FastAPIAdapterErrorLocation | None = None,
    ) -> FastAPIAdapterErrorPayload:
        """Builds one payload with a single normalized detail item.

        Returns:
            A normalized FastAPI adapter payload.
        """
        return cls(
            parameter=parameter_name,
            error_type=error_type,
            details=(
                FastAPIAdapterErrorDetail(
                    code=code,
                    detail=detail,
                    field=field,
                    location=location,
                ),
            ),
        )

    @classmethod
    def from_query_error(
        cls,
        parameter_name: str,
        error: ParseError | SemanticError,
    ) -> FastAPIAdapterErrorPayload:
        """Builds a payload for one filter/query parsing or semantic error.

        Returns:
            A normalized FastAPI adapter payload.
        """
        error_type = "query_parse_error"
        detail_code = getattr(error, "code", "query_parse_error")
        detail_field = None
        detail_location = None
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
            detail_location = _build_error_location(error.span)
        elif isinstance(error, ParseError):
            detail_location = _build_error_location(error.span)
        return cls._single_detail_payload(
            parameter_name=parameter_name,
            error_type=error_type,
            code=detail_code,
            detail=error.message,
            field=detail_field,
            location=detail_location,
        )

    @classmethod
    def from_sort_error(
        cls,
        parameter_name: str,
        error: SortAdapterError,
    ) -> FastAPIAdapterErrorPayload:
        """Builds a payload for one sort parsing or semantic error.

        Returns:
            A normalized FastAPI adapter payload.
        """
        error_type = "sort_parse_error"
        detail_code = getattr(error, "code", "sort_parse_error")
        detail_message = getattr(error, "message", str(error))
        detail_field = None
        if isinstance(
            error,
            (
                SortFieldNotWhitelistedError,
                SortFieldBlacklistedError,
                SortFunctionNotWhitelistedError,
                SortFunctionBlacklistedError,
            ),
        ):
            error_type = "sort_semantic_error"
            detail_field = _extract_field_from_message(detail_message)
        return cls._single_detail_payload(
            parameter_name=parameter_name,
            error_type=error_type,
            code=detail_code,
            detail=detail_message,
            field=detail_field,
        )

    @classmethod
    def from_page_error(
        cls,
        parameter_name: str,
        *,
        error_type: str,
        detail_code: str,
        message: str,
    ) -> FastAPIAdapterErrorPayload:
        """Builds a payload for one page-related adapter validation error.

        Returns:
            A normalized FastAPI adapter payload.
        """
        return cls._single_detail_payload(
            parameter_name=parameter_name,
            error_type=error_type,
            code=detail_code,
            detail=message,
        )

    @classmethod
    def from_backend_error(
        cls,
        parameter_name: str,
        *,
        error_type: str,
        error: ORMError,
    ) -> FastAPIAdapterErrorPayload:
        """Builds a payload for one ORM backend integration failure.

        Returns:
            A normalized FastAPI adapter payload.
        """
        error_message = str(error)
        return cls._single_detail_payload(
            parameter_name=parameter_name,
            error_type=error_type,
            code=getattr(error, "code", "orm_error"),
            detail=error_message,
            field=_extract_field_from_message(error_message),
        )

    def to_http_detail(self) -> dict[str, object]:
        """Builds the ``HTTPException.detail`` payload for this adapter error.

        Returns:
            A JSON-compatible FastAPI error detail mapping.
        """
        problem_definition = _problem_definition(self.error_type)
        return {
            "type": problem_definition.type_uri,
            "title": problem_definition.title,
            "parameter": self.parameter,
            "detail": _top_level_detail(problem_definition.title, self.details),
            "errors": list(msgspec.to_builtins(self.details)),
        }

    @property
    def status_code(self) -> int:
        """Returns the HTTP status code associated with this problem."""
        return _problem_definition(self.error_type).status


class _ProblemDefinition(msgspec.Struct, frozen=True, gc=False):
    """Stable definition for one top-level adapter problem category."""

    type_uri: str
    title: str
    status: int


class FastAPIAdapterErrorLocation(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
):
    """Structured source location exposed by adapter diagnostics."""

    index: int
    line: int
    column: int


class FastAPIAdapterErrorDetail(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
):
    """Structured detail item exposed in FastAPI adapter responses."""

    code: str
    detail: str
    field: str | None = None
    location: FastAPIAdapterErrorLocation | None = None


_PROBLEM_DEFINITIONS = {
    "page_configuration_error": _ProblemDefinition(
        type_uri="urn:pyrsql:problem:page-configuration-error",
        title="Page configuration error",
        status=400,
    ),
    "page_validation_error": _ProblemDefinition(
        type_uri="urn:pyrsql:problem:page-validation-error",
        title="Page validation error",
        status=400,
    ),
    "query_backend_error": _ProblemDefinition(
        type_uri="urn:pyrsql:problem:query-backend-error",
        title="Query backend error",
        status=422,
    ),
    "query_parse_error": _ProblemDefinition(
        type_uri="urn:pyrsql:problem:query-parse-error",
        title="Query parse error",
        status=400,
    ),
    "query_semantic_error": _ProblemDefinition(
        type_uri="urn:pyrsql:problem:query-semantic-error",
        title="Query semantic error",
        status=422,
    ),
    "sort_backend_error": _ProblemDefinition(
        type_uri="urn:pyrsql:problem:sort-backend-error",
        title="Sort backend error",
        status=422,
    ),
    "sort_parse_error": _ProblemDefinition(
        type_uri="urn:pyrsql:problem:sort-parse-error",
        title="Sort parse error",
        status=400,
    ),
    "sort_semantic_error": _ProblemDefinition(
        type_uri="urn:pyrsql:problem:sort-semantic-error",
        title="Sort semantic error",
        status=422,
    ),
}


def _problem_definition(error_type: str) -> _ProblemDefinition:
    """Returns the top-level problem definition for one category."""
    return _PROBLEM_DEFINITIONS[error_type]


def _top_level_detail(
    title: str,
    details: tuple[FastAPIAdapterErrorDetail, ...],
) -> str:
    """Builds the top-level problem detail summary.

    Returns:
        One summary detail for the problem payload.
    """
    if len(details) == 1:
        return details[0].detail
    return title


def _extract_field_from_message(message: str) -> str | None:
    """Extracts a quoted field path from a normalized pyrsql message.

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


def _build_error_location(
    span: SourceSpan,
) -> FastAPIAdapterErrorLocation:
    """Builds one adapter-facing location from a source span.

    Returns:
        One normalized adapter-facing source location.
    """
    return FastAPIAdapterErrorLocation(
        index=span.start.index,
        line=span.start.line,
        column=span.start.column,
    )
