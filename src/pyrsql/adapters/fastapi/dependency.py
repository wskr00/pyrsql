"""Dependency factories for FastAPI request integration."""

from inspect import signature
from typing import TYPE_CHECKING, Annotated, NoReturn

try:
    from fastapi import HTTPException, Query
except ImportError as error:  # pragma: no cover - import guard
    raise ImportError(
        "FastAPI support requires installing the 'fastapi' extra: "
        "pip install pyrsql[fastapi]",
    ) from error

from pyrsql.adapters.fastapi.config import (
    FastAPICriteriaConfig,
    SortParameterFormat,
)
from pyrsql.adapters.fastapi.criteria import RequestCriteria
from pyrsql.adapters.fastapi.errors import (
    FastAPIAdapterErrorPayload,
)
from pyrsql.core.page import PageRequest
from pyrsql.core.query import Query as PyrsqlQuery
from pyrsql.core.sort import Sort as PyrsqlSort
from pyrsql.parsing.errors import ParseError
from pyrsql.semantic.errors import SemanticError
from pyrsql.sorting.errors import (
    SortFieldBlacklistedError,
    SortFieldNotWhitelistedError,
    SortFunctionBlacklistedError,
    SortFunctionNotWhitelistedError,
    SortParseError,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from inspect import Signature

_QUERY_ERROR_TYPES = (ParseError, SemanticError)
_SORT_ERROR_TYPES = (
    SortParseError,
    SortFieldNotWhitelistedError,
    SortFieldBlacklistedError,
    SortFunctionNotWhitelistedError,
    SortFunctionBlacklistedError,
)
_DEFAULT_FASTAPI_CRITERIA_CONFIG = FastAPICriteriaConfig()


def _raise_http_error(
    payload: "FastAPIAdapterErrorPayload",  # noqa: UP037
) -> NoReturn:
    """Raises a standardized FastAPI HTTP exception for adapter failures.

    Raises:
        HTTPException: Always raised with a normalized adapter payload.
    """
    raise HTTPException(
        status_code=payload.status_code,
        detail=payload.to_http_detail(),
    )


def _build_page_request(
    *,
    config: FastAPICriteriaConfig,
    page_value: int | None,
    size_value: int | None,
) -> PageRequest | None:
    """Builds a page request from validated FastAPI query params.

    Returns:
        A normalized page request, or ``None`` when pagination is absent.

    """
    resolved_page_size = (
        config.default_page_size if size_value is None else size_value
    )

    if page_value is None:
        if resolved_page_size is None:
            return None
        resolved_page_number = config.default_page_number
    else:
        resolved_page_number = page_value

    if resolved_page_size is None:
        _raise_http_error(
            FastAPIAdapterErrorPayload.from_page_error(
                config.size_parameter,
                error_type="page_configuration_error",
                detail_code="missing_page_size",
                message=(
                    f"'{config.size_parameter}' is required when "
                    f"'{config.page_parameter}' is provided."
                ),
            ),
        )

    if config.one_based_paging:
        resolved_page_number -= 1

    return PageRequest.of(
        resolved_page_number,
        resolved_page_size,
    )


def _build_request_criteria(
    *,
    config: FastAPICriteriaConfig,
    filter_value: str | None,
    sort_value: str | None,
    page_value: int | None,
    size_value: int | None,
) -> RequestCriteria:
    """Builds criteria from values already extracted by FastAPI.

    Returns:
        The parsed request criteria.
    """
    query = None
    sort = None

    if filter_value:
        try:
            query = PyrsqlQuery.parse(
                filter_value,
                options=config.query_options,
            )
        except _QUERY_ERROR_TYPES as error:
            _raise_http_error(
                FastAPIAdapterErrorPayload.from_query_error(
                    config.filter_parameter,
                    error,
                ),
            )

    if sort_value:
        try:
            sort = PyrsqlSort.parse(
                sort_value,
                options=config.sort_options,
            )
        except _SORT_ERROR_TYPES as error:
            _raise_http_error(
                FastAPIAdapterErrorPayload.from_sort_error(
                    config.sort_parameter,
                    error,
                ),
            )

    return RequestCriteria(
        query=query,
        sort=sort,
        page_request=_build_page_request(
            config=config,
            page_value=page_value,
            size_value=size_value,
        ),
    )


def _build_criteria_callable(
    config: FastAPICriteriaConfig,
) -> "Callable[..., RequestCriteria]":  # noqa: UP037
    """Builds the concrete dependency callable for a fixed configuration.

    Returns:
        A FastAPI-compatible callable with the configured sort format.
    """
    if config.sort_parameter_format is SortParameterFormat.REPEATED:
        return _build_repeated_sort_criteria_callable(config)
    return _build_semicolon_sort_criteria_callable(config)


def _build_semicolon_sort_criteria_callable(
    config: FastAPICriteriaConfig,
) -> "Callable[..., RequestCriteria]":  # noqa: UP037
    """Builds a dependency that accepts one semicolon-delimited sort value.

    Returns:
        A FastAPI-compatible callable.
    """

    def dependency(
        filter_value: Annotated[
            str | None,
            Query(
                alias=config.filter_parameter,
                openapi_examples=config.filter_openapi_examples or None,
            ),
        ] = None,
        sort_value: Annotated[
            str | None,
            Query(
                alias=config.sort_parameter,
                openapi_examples=config.sort_openapi_examples or None,
            ),
        ] = None,
        page_value: Annotated[
            int | None,
            Query(
                alias=config.page_parameter,
                ge=config.minimum_page_number,
                openapi_examples=config.page_openapi_examples or None,
            ),
        ] = None,
        size_value: Annotated[
            int | None,
            Query(
                alias=config.size_parameter,
                gt=0,
                le=config.max_page_size,
                openapi_examples=config.size_openapi_examples or None,
            ),
        ] = None,
    ) -> RequestCriteria:
        return _build_request_criteria(
            config=config,
            filter_value=filter_value,
            sort_value=sort_value,
            page_value=page_value,
            size_value=size_value,
        )

    return dependency


def _build_repeated_sort_criteria_callable(
    config: FastAPICriteriaConfig,
) -> "Callable[..., RequestCriteria]":  # noqa: UP037
    """Builds a dependency that accepts repeated sort query parameters.

    Returns:
        A FastAPI-compatible callable.
    """

    def dependency(
        filter_value: Annotated[
            str | None,
            Query(
                alias=config.filter_parameter,
                openapi_examples=config.filter_openapi_examples or None,
            ),
        ] = None,
        sort_values: Annotated[
            list[str] | None,
            Query(
                alias=config.sort_parameter,
                openapi_examples=config.sort_openapi_examples or None,
            ),
        ] = None,
        page_value: Annotated[
            int | None,
            Query(
                alias=config.page_parameter,
                ge=config.minimum_page_number,
                openapi_examples=config.page_openapi_examples or None,
            ),
        ] = None,
        size_value: Annotated[
            int | None,
            Query(
                alias=config.size_parameter,
                gt=0,
                le=config.max_page_size,
                openapi_examples=config.size_openapi_examples or None,
            ),
        ] = None,
    ) -> RequestCriteria:
        return _build_request_criteria(
            config=config,
            filter_value=filter_value,
            sort_value=";".join(sort_values) if sort_values else None,
            page_value=page_value,
            size_value=size_value,
        )

    return dependency


class CriteriaDependency:
    """Callable FastAPI dependency object that resolves request criteria.

    The generated signature exposes FastAPI query parameters and returns a
    parsed RequestCriteria object.
    """

    __slots__ = ("__signature__", "_dependency", "config")

    def __init__(
        self,
        config: FastAPICriteriaConfig | None = None,
    ) -> None:
        """Creates a dependency object for the provided FastAPI config.

        Args:
            config: Optional FastAPI criteria configuration.
        """
        self.config = (
            _DEFAULT_FASTAPI_CRITERIA_CONFIG if config is None else config
        )
        self._dependency = _build_criteria_callable(self.config)
        self.__signature__: Signature = signature(self._dependency)

    def __call__(self, *args: object, **kwargs: object) -> RequestCriteria:
        """Delegates FastAPI dependency resolution to the generated callable.

        Returns:
            Parsed request criteria for the incoming FastAPI query params.
        """
        return self._dependency(*args, **kwargs)


def criteria_dependency(
    config: FastAPICriteriaConfig | None = None,
) -> CriteriaDependency:
    """Builds a FastAPI dependency object that returns parsed criteria.

    Args:
        config: Optional FastAPI criteria configuration.

    Returns:
        A callable FastAPI dependency object.
    """
    if config is None:
        return _DEFAULT_CRITERIA_DEPENDENCY
    return CriteriaDependency(config)


_DEFAULT_CRITERIA_DEPENDENCY = CriteriaDependency(
    _DEFAULT_FASTAPI_CRITERIA_CONFIG,
)
