"""Configuration objects for the FastAPI adapter."""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

import msgspec

from pyrsql.core.options import QueryOptions, SortOptions
from pyrsql.core.validation import validate_positive_int

_DEFAULT_FILTER_PARAMETER = "filter"
_DEFAULT_SORT_PARAMETER = "sort"
_DEFAULT_PAGE_PARAMETER = "page"
_DEFAULT_SIZE_PARAMETER = "size"
_DEFAULT_QUERY_OPTIONS = QueryOptions()
_DEFAULT_SORT_OPTIONS = SortOptions()
_EMPTY_OPENAPI_EXAMPLES: Mapping[str, Any] = MappingProxyType({})


def _normalize_parameter_name(name: object, *, field_name: str) -> str:
    """Validates and normalizes one public FastAPI parameter name.

    Returns:
        The validated parameter name.

    Raises:
        TypeError: If the parameter name is not a string.
        ValueError: If the parameter name is empty or has outer whitespace.
    """
    if not isinstance(name, str):
        raise TypeError(f"{field_name} must be a string.")
    normalized_name = name.strip()
    if not normalized_name:
        raise ValueError("FastAPI parameter names must not be empty.")
    if normalized_name != name:
        raise ValueError(
            "FastAPI parameter names must not contain outer whitespace.",
        )
    return normalized_name


def _normalize_openapi_examples_mapping(
    value: object,
    *,
    field_name: str,
) -> Mapping[str, Any]:
    """Validates and freezes one OpenAPI examples mapping.

    Returns:
        An immutable copy of the provided examples mapping.

    Raises:
        TypeError: If the provided value is not a mapping.
    """
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping instance.")
    return MappingProxyType(dict(value))


class FastAPICriteriaConfig(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
):
    """Configures FastAPI query parameter extraction for pyrsql.

    Attributes:
        filter_parameter: Query parameter used for filtering expressions.
        sort_parameter: Query parameter used for sort expressions.
        page_parameter: Query parameter used for page numbers.
        size_parameter: Query parameter used for page size.
        default_page_size: Default size used when only a page number is given.
        max_page_size: Maximum accepted page size.
        one_based_paging: Whether page numbers start at 1 instead of 0.
        query_options: Query parsing and semantic configuration.
        sort_options: Sort parsing and semantic configuration.
    """

    filter_parameter: str = _DEFAULT_FILTER_PARAMETER
    sort_parameter: str = _DEFAULT_SORT_PARAMETER
    page_parameter: str = _DEFAULT_PAGE_PARAMETER
    size_parameter: str = _DEFAULT_SIZE_PARAMETER
    default_page_size: int | None = None
    max_page_size: int | None = None
    one_based_paging: bool = False
    query_options: QueryOptions = _DEFAULT_QUERY_OPTIONS
    sort_options: SortOptions = _DEFAULT_SORT_OPTIONS
    filter_openapi_examples: Mapping[str, Any] = _EMPTY_OPENAPI_EXAMPLES
    sort_openapi_examples: Mapping[str, Any] = _EMPTY_OPENAPI_EXAMPLES
    page_openapi_examples: Mapping[str, Any] = _EMPTY_OPENAPI_EXAMPLES
    size_openapi_examples: Mapping[str, Any] = _EMPTY_OPENAPI_EXAMPLES

    def __post_init__(self) -> None:
        """Validates adapter configuration invariants.

        Raises:
            ValueError: If parameter names are empty, duplicated, or paging
                limits are inconsistent.
        """
        parameter_names = (
            _normalize_parameter_name(
                self.filter_parameter,
                field_name="filter_parameter",
            ),
            _normalize_parameter_name(
                self.sort_parameter,
                field_name="sort_parameter",
            ),
            _normalize_parameter_name(
                self.page_parameter,
                field_name="page_parameter",
            ),
            _normalize_parameter_name(
                self.size_parameter,
                field_name="size_parameter",
            ),
        )
        if len(set(parameter_names)) != len(parameter_names):
            raise ValueError("FastAPI parameter names must be unique.")
        if self.default_page_size is not None:
            validate_positive_int(
                self.default_page_size,
                field_name="default_page_size",
            )
        if self.max_page_size is not None:
            validate_positive_int(
                self.max_page_size,
                field_name="max_page_size",
            )
        if (
            self.default_page_size is not None
            and self.max_page_size is not None
            and self.default_page_size > self.max_page_size
        ):
            raise ValueError("default_page_size must not exceed max_page_size.")
        for field_name in (
            "filter_openapi_examples",
            "sort_openapi_examples",
            "page_openapi_examples",
            "size_openapi_examples",
        ):
            msgspec.structs.force_setattr(
                self,
                field_name,
                _normalize_openapi_examples_mapping(
                    getattr(self, field_name),
                    field_name=field_name,
                ),
            )

    @property
    def minimum_page_number(self) -> int:
        """The minimum accepted page number for the adapter.

        Returns:
            The lowest valid page number accepted by the adapter.
        """
        return 1 if self.one_based_paging else 0

    @property
    def default_page_number(self) -> int:
        """The page number used when only size is provided.

        Returns:
            The implicit page number used when only page size is provided.
        """
        return 1 if self.one_based_paging else 0
