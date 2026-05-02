"""Configuration objects for the FastAPI adapter."""

from dataclasses import dataclass, field

from pyrsql.core.options import QueryOptions, SortOptions

_DEFAULT_FILTER_PARAMETER = "filter"
_DEFAULT_SORT_PARAMETER = "sort"
_DEFAULT_PAGE_PARAMETER = "page"
_DEFAULT_SIZE_PARAMETER = "size"


@dataclass(frozen=True, slots=True)
class FastAPICriteriaConfig:
    """Configures FastAPI query parameter extraction for pyrsql."""

    filter_parameter: str = _DEFAULT_FILTER_PARAMETER
    sort_parameter: str = _DEFAULT_SORT_PARAMETER
    page_parameter: str = _DEFAULT_PAGE_PARAMETER
    size_parameter: str = _DEFAULT_SIZE_PARAMETER
    default_page_size: int | None = None
    max_page_size: int | None = None
    one_based_paging: bool = False
    query_options: QueryOptions = field(default_factory=QueryOptions)
    sort_options: SortOptions = field(default_factory=SortOptions)

    def __post_init__(self) -> None:
        """Validates adapter configuration invariants."""
        parameter_names = (
            self.filter_parameter,
            self.sort_parameter,
            self.page_parameter,
            self.size_parameter,
        )
        normalized_names = tuple(name.strip() for name in parameter_names)
        if any(not name for name in normalized_names):
            raise ValueError("FastAPI parameter names must not be empty.")
        if len(set(normalized_names)) != len(normalized_names):
            raise ValueError("FastAPI parameter names must be unique.")
        if self.default_page_size is not None and self.default_page_size <= 0:
            raise ValueError("default_page_size must be greater than 0.")
        if self.max_page_size is not None and self.max_page_size <= 0:
            raise ValueError("max_page_size must be greater than 0.")
        if (
            self.default_page_size is not None
            and self.max_page_size is not None
            and self.default_page_size > self.max_page_size
        ):
            raise ValueError("default_page_size must not exceed max_page_size.")

    @property
    def minimum_page_number(self) -> int:
        """Returns the minimum accepted page number for the adapter."""
        return 1 if self.one_based_paging else 0

    @property
    def default_page_number(self) -> int:
        """Returns the page number used when only size is provided."""
        return 1 if self.one_based_paging else 0
