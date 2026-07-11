"""Configuration objects for the FastAPI adapter."""

from __future__ import annotations

from enum import Enum
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import msgspec

from pyrsql.core.options import QueryOptions, SortOptions

if TYPE_CHECKING:
    from collections.abc import Mapping

_DEFAULT_FILTER_PARAMETER = "filter"
_DEFAULT_SORT_PARAMETER = "sort"
_DEFAULT_PAGE_PARAMETER = "page"
_DEFAULT_SIZE_PARAMETER = "size"
_DEFAULT_QUERY_OPTIONS = QueryOptions()
_DEFAULT_SORT_OPTIONS = SortOptions()
_EMPTY_OPENAPI_EXAMPLES: Mapping[str, Any] = MappingProxyType({})


class SortParameterFormat(Enum):
    """Supported HTTP representations for sort criteria."""

    SEMICOLON = "semicolon"
    REPEATED = "repeated"


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
        sort_parameter_format: HTTP representation accepted for sort criteria.
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
    sort_parameter_format: SortParameterFormat = SortParameterFormat.SEMICOLON
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
