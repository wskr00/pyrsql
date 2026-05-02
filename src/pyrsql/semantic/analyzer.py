"""Backend-neutral semantic analysis."""

from pyrsql.core.options import QueryOptions
from pyrsql.parsing.ast import ComparisonNode
from pyrsql.parsing.ast import Expression
from pyrsql.parsing.ast import LogicalNode
from pyrsql.selector.analyzer import SelectorSemanticAnalyzer
from pyrsql.selector.ast import Selector
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
        self._field_whitelist = options.field_whitelist
        self._field_blacklist = options.field_blacklist
        self._procedure_policy = options.procedure_policy
        self._selector_analyzer = SelectorSemanticAnalyzer(
            options.field_mapping
        )

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
        return self._selector_analyzer.analyze(
            selector,
            validate_field=lambda field_path: self._enforce_field_access_policy(
                field_path,
                expression,
            ),
            validate_function=(
                lambda function_name: self._enforce_function_access_policy(
                    function_name,
                    expression=expression,
                )
            ),
        )

    def _enforce_field_access_policy(
        self,
        field_path: str,
        expression: ComparisonNode,
    ) -> None:
        """Validates whitelist and blacklist rules."""
        if self._field_whitelist and field_path not in self._field_whitelist:
            raise FieldNotWhitelistedError(
                message=f"Field {field_path!r} is not allowed",
                span=expression.span,
            )
        if field_path in self._field_blacklist:
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
        if not self._procedure_policy.is_whitelisted(function_name):
            raise FunctionNotWhitelistedError(
                message=f"Function {function_name!r} is not whitelisted",
                span=expression.span,
            )
        if self._procedure_policy.is_blacklisted(function_name):
            raise FunctionBlacklistedError(
                message=f"Function {function_name!r} is blacklisted",
                span=expression.span,
            )
