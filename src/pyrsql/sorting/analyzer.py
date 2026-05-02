"""Semantic analysis for sort expressions."""

from pyrsql.core.options import SortOptions
from pyrsql.selector.ast import ColumnSelector
from pyrsql.selector.ast import FunctionSelector
from pyrsql.selector.ast import LiteralSelector
from pyrsql.selector.ast import Selector
from pyrsql.selector.semantic import SemanticColumnSelector
from pyrsql.selector.semantic import SemanticFunctionSelector
from pyrsql.selector.semantic import SemanticLiteralSelector
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
        self._options = options

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
        if isinstance(selector, ColumnSelector):
            field_path = self._options.field_mapping.get(
                selector.selector,
                selector.selector,
            )
            self._validate_field_access(field_path)
            return SemanticColumnSelector(
                selector=selector.selector,
                field_path=field_path,
            )
        if isinstance(selector, LiteralSelector):
            return SemanticLiteralSelector(value=selector.value)
        self._validate_function_access(selector.function_name)
        assert isinstance(selector, FunctionSelector)
        return SemanticFunctionSelector(
            function_name=selector.function_name,
            arguments=tuple(
                self._analyze_selector(argument)
                for argument in selector.arguments
            ),
        )

    def _validate_field_access(self, field_path: str) -> None:
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

    def _validate_function_access(self, function_name: str) -> None:
        """Validates whitelist and blacklist rules for a sort function."""
        procedure_policy = self._options.procedure_policy
        if not procedure_policy.is_whitelisted(function_name):
            raise SortFunctionNotWhitelistedError(
                f"Function {function_name!r} is not whitelisted."
            )
        if procedure_policy.is_blacklisted(function_name):
            raise SortFunctionBlacklistedError(
                f"Function {function_name!r} is blacklisted."
            )
