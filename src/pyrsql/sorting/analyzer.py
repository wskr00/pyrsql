"""Semantic analysis for sort expressions."""

from pyrsql.core.options import SortOptions
from pyrsql.selector.analyzer import SelectorSemanticAnalyzer
from pyrsql.selector.ast import Selector
from pyrsql.selector.semantic import SemanticSelector
from pyrsql.sorting.ast import SortField
from pyrsql.sorting.errors import SortFieldBlacklistedError
from pyrsql.sorting.errors import SortFieldNotWhitelistedError
from pyrsql.sorting.errors import SortFunctionBlacklistedError
from pyrsql.sorting.errors import SortFunctionNotWhitelistedError
from pyrsql.sorting.semantic import SemanticSortField


class SortAnalyzer:
    """Applies selector mapping and access rules to parsed sort fields."""

    def __init__(self, options: SortOptions) -> None:
        self._field_whitelist = options.field_whitelist
        self._field_blacklist = options.field_blacklist
        self._procedure_policy = options.procedure_policy
        self._selector_analyzer = SelectorSemanticAnalyzer(
            options.field_mapping
        )

    def analyze(
        self,
        fields: tuple[SortField, ...],
    ) -> tuple[SemanticSortField, ...]:
        """Analyzes parsed sort fields into semantic sort fields."""
        return tuple(self._analyze_field(field) for field in fields)

    def _analyze_field(self, field: SortField) -> SemanticSortField:
        """Analyzes a single parsed sort field."""
        return SemanticSortField(
            selector=self._analyze_selector(field.selector),
            direction=field.direction,
            ignore_case=field.ignore_case,
        )

    def _analyze_selector(
        self,
        selector: Selector,
    ) -> SemanticSelector:
        """Analyzes a parsed selector recursively."""
        return self._selector_analyzer.analyze(
            selector,
            validate_field=self._validate_field_access,
            validate_function=self._validate_function_access,
        )

    def _validate_field_access(self, field_path: str) -> None:
        """Validates whitelist and blacklist rules for a sort field."""
        if self._field_whitelist and field_path not in self._field_whitelist:
            raise SortFieldNotWhitelistedError(
                f"Field {field_path!r} is not allowed by the whitelist."
            )
        if field_path in self._field_blacklist:
            raise SortFieldBlacklistedError(
                f"Field {field_path!r} is blocked by the blacklist."
            )

    def _validate_function_access(self, function_name: str) -> None:
        """Validates whitelist and blacklist rules for a sort function."""
        if not self._procedure_policy.is_whitelisted(function_name):
            raise SortFunctionNotWhitelistedError(
                f"Function {function_name!r} is not whitelisted."
            )
        if self._procedure_policy.is_blacklisted(function_name):
            raise SortFunctionBlacklistedError(
                f"Function {function_name!r} is blacklisted."
            )
