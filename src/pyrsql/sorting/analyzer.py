"""Semantic analysis for sort expressions."""

from pyrsql.core.options import SortOptions
from pyrsql.sorting.ast import SortField
from pyrsql.sorting.errors import SortFieldBlacklistedError
from pyrsql.sorting.errors import SortFieldNotWhitelistedError
from pyrsql.sorting.semantic import SemanticSortField


class SortAnalyzer:
    """Applies selector mapping and access rules to parsed sort fields."""

    def __init__(self, options: SortOptions) -> None:
        self._options = options

    def analyze(
        self,
        fields: tuple[SortField, ...],
    ) -> tuple[SemanticSortField, ...]:
        """Analyzes parsed sort fields into semantic sort fields."""
        return tuple(self._analyze_field(field) for field in fields)

    def _analyze_field(self, field: SortField) -> SemanticSortField:
        """Analyzes a single parsed sort field."""
        field_path = self._options.field_mapping.get(
            field.selector,
            field.selector,
        )
        self._validate_access(field_path)
        return SemanticSortField(
            selector=field.selector,
            field_path=field_path,
            direction=field.direction,
            ignore_case=field.ignore_case,
        )

    def _validate_access(self, field_path: str) -> None:
        """Validates whitelist and blacklist rules for a sort field."""
        whitelist = self._options.field_whitelist
        blacklist = self._options.field_blacklist
        if whitelist and field_path not in whitelist:
            raise SortFieldNotWhitelistedError(
                f"Field {field_path!r} is not allowed by the whitelist."
            )
        if field_path in blacklist:
            raise SortFieldBlacklistedError(
                f"Field {field_path!r} is blocked by the blacklist."
            )
