"""Backend-neutral semantic analysis."""

import re

from pyrsql.core.options import QueryOptions
from pyrsql.parsing.ast import ComparisonNode
from pyrsql.parsing.ast import Expression
from pyrsql.parsing.ast import LogicalNode
from pyrsql.selector.ast import ColumnSelector
from pyrsql.selector.ast import FunctionSelector
from pyrsql.selector.ast import LiteralSelector
from pyrsql.selector.ast import Selector
from pyrsql.selector.semantic import SemanticColumnSelector
from pyrsql.selector.semantic import SemanticFunctionSelector
from pyrsql.selector.semantic import SemanticLiteralSelector
from pyrsql.selector.semantic import SemanticSelector
from pyrsql.semantic.ast import SemanticComparison
from pyrsql.semantic.ast import SemanticExpression
from pyrsql.semantic.ast import SemanticLogical
from pyrsql.semantic.errors import FieldBlacklistedError
from pyrsql.semantic.errors import FieldNotWhitelistedError
from pyrsql.semantic.errors import FunctionBlacklistedError
from pyrsql.semantic.errors import FunctionNotWhitelistedError


class SemanticAnalyzer:
    """Applies backend-neutral semantic rules to parsed expressions."""

    def __init__(self, options: QueryOptions) -> None:
        self._options = options

    def analyze(self, expression: Expression) -> SemanticExpression:
        """Analyzes a parsed AST into a semantic expression tree."""
        if isinstance(expression, ComparisonNode):
            return self._analyze_comparison(expression)
        assert isinstance(expression, LogicalNode)
        return SemanticLogical(
            span=expression.span,
            operator=expression.operator,
            children=tuple(
                self.analyze(child) for child in expression.children
            ),
        )

    def _analyze_comparison(
        self,
        expression: ComparisonNode,
    ) -> SemanticComparison:
        """Analyzes a comparison node."""
        return SemanticComparison(
            span=expression.span,
            selector=self._analyze_selector(
                expression.selector,
                expression=expression,
            ),
            operator=expression.operator,
            arguments=expression.arguments,
        )

    def _analyze_selector(
        self,
        selector: Selector,
        *,
        expression: ComparisonNode,
    ) -> SemanticSelector:
        """Analyzes a parsed selector recursively."""
        if isinstance(selector, ColumnSelector):
            field_path = self._options.field_mapping.get(
                selector.selector,
                selector.selector,
            )
            self._enforce_field_access_policy(field_path, expression)
            return SemanticColumnSelector(
                selector=selector.selector,
                field_path=field_path,
            )
        if isinstance(selector, LiteralSelector):
            return SemanticLiteralSelector(value=selector.value)
        assert isinstance(selector, FunctionSelector)
        self._enforce_function_access_policy(
            selector.function_name,
            expression=expression,
        )
        return SemanticFunctionSelector(
            function_name=selector.function_name,
            arguments=tuple(
                self._analyze_selector(argument, expression=expression)
                for argument in selector.arguments
            ),
        )

    def _enforce_field_access_policy(
        self,
        field_path: str,
        expression: ComparisonNode,
    ) -> None:
        """Validates whitelist and blacklist rules."""
        if (
            self._options.field_whitelist
            and field_path not in self._options.field_whitelist
        ):
            raise FieldNotWhitelistedError(
                message=f"Field {field_path!r} is not allowed",
                span=expression.span,
            )
        if field_path in self._options.field_blacklist:
            raise FieldBlacklistedError(
                message=f"Field {field_path!r} is blocked",
                span=expression.span,
            )

    def _enforce_function_access_policy(
        self,
        function_name: str,
        *,
        expression: ComparisonNode,
    ) -> None:
        """Validates whitelist and blacklist rules for functions."""
        if not self._matches_any(
            function_name,
            self._options.procedure_whitelist,
        ):
            raise FunctionNotWhitelistedError(
                message=f"Function {function_name!r} is not whitelisted",
                span=expression.span,
            )
        if self._matches_any(
            function_name,
            self._options.procedure_blacklist,
        ):
            raise FunctionBlacklistedError(
                message=f"Function {function_name!r} is blacklisted",
                span=expression.span,
            )

    def _matches_any(self, value: str, patterns: tuple[str, ...]) -> bool:
        """Returns whether a value fully matches at least one regex."""
        return any(re.fullmatch(pattern, value) for pattern in patterns)
