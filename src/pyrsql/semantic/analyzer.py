"""Backend-neutral semantic analysis."""

from pyrsql.core.options import QueryOptions
from pyrsql.parsing.ast import ComparisonNode
from pyrsql.parsing.ast import Expression
from pyrsql.parsing.ast import LogicalNode
from pyrsql.semantic.ast import SemanticComparison
from pyrsql.semantic.ast import SemanticExpression
from pyrsql.semantic.ast import SemanticLogical
from pyrsql.semantic.errors import FieldBlacklistedError
from pyrsql.semantic.errors import FieldNotWhitelistedError


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
        field_path = self._resolve_field_path(expression.selector)
        self._enforce_access_policy(field_path, expression)
        return SemanticComparison(
            span=expression.span,
            selector=expression.selector,
            field_path=field_path,
            operator=expression.operator,
            arguments=expression.arguments,
        )

    def _resolve_field_path(self, selector: str) -> str:
        """Resolves field aliases into canonical field paths."""
        return self._options.field_mapping.get(selector, selector)

    def _enforce_access_policy(
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
