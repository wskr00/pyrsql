"""ORM-neutral semantic binder."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrsql.core.binding_policy import (
    MappedFieldBindingOptions,
    enforce_field_access_policy,
    enforce_function_access_policy,
)
from pyrsql.parsing.ast import ComparisonNode, LogicalNode
from pyrsql.selector.ast import (
    FieldSelector,
    FunctionSelector,
    LiteralSelector,
)
from pyrsql.semantic.errors import (
    FieldBlacklistedError,
    FieldNotWhitelistedError,
    FunctionBlacklistedError,
    FunctionNotWhitelistedError,
)

if TYPE_CHECKING:
    from pyrsql.parsing.ast import Expression
    from pyrsql.parsing.source import SourceSpan
    from pyrsql.selector.ast import (
        SelectorNode,
    )


class SemanticBinder:
    """Normalizes parsed query AST nodes after semantic checks."""

    def __init__(self, options: MappedFieldBindingOptions) -> None:
        """Initializes the binder with semantic binding options."""
        self._field_whitelist = options.field_whitelist
        self._field_blacklist = options.field_blacklist
        self._procedure_policy = options.procedure_policy
        self._field_mapping = options.field_mapping

    def bind(self, expression: Expression) -> Expression:
        """Normalizes a parsed AST after semantic validation.

        Returns:
            A semantically validated expression tree.

        """
        if isinstance(expression, ComparisonNode):
            return self._bind_comparison(expression)
        return LogicalNode(
            span=expression.span,
            operator=expression.operator,
            children=tuple(self.bind(child) for child in expression.children),
        )

    def _bind_comparison(
        self,
        expression: ComparisonNode,
    ) -> ComparisonNode:
        """Normalizes a parsed comparison node.

        Returns:
            The semantically validated comparison node.
        """
        return ComparisonNode(
            span=expression.span,
            selector=self._bind_selector(
                expression.selector,
                span=expression.span,
            ),
            operator=expression.operator,
            arguments=expression.arguments,
        )

    def _bind_selector(
        self,
        selector: SelectorNode,
        *,
        span: SourceSpan,
    ) -> SelectorNode:
        """Normalizes a parsed selector recursively.

        Returns:
            The semantically validated selector node.

        """
        if isinstance(selector, FieldSelector):
            field_path = self._field_mapping.get(
                selector.raw_path,
                selector.raw_path,
            )
            self._enforce_field_access_policy(field_path, span)
            return FieldSelector(
                raw_path=field_path,
            )
        if isinstance(selector, LiteralSelector):
            return selector
        self._enforce_function_access_policy(selector.function_name, span=span)
        return FunctionSelector(
            function_name=selector.function_name,
            arguments=tuple(
                self._bind_selector(argument, span=span)
                for argument in selector.arguments
            ),
        )

    def _enforce_field_access_policy(
        self,
        field_path: str,
        span: SourceSpan,
    ) -> None:
        """Validates whitelist and blacklist rules."""
        enforce_field_access_policy(
            field_path,
            field_whitelist=self._field_whitelist,
            field_blacklist=self._field_blacklist,
            not_whitelisted_error_factory=lambda message: (
                FieldNotWhitelistedError(message=message, span=span)
            ),
            blacklisted_error_factory=lambda message: FieldBlacklistedError(
                message=message, span=span
            ),
        )

    def _enforce_function_access_policy(
        self,
        function_name: str,
        *,
        span: SourceSpan,
    ) -> None:
        """Validates whitelist and blacklist rules for functions."""
        enforce_function_access_policy(
            function_name,
            procedure_policy=self._procedure_policy,
            not_whitelisted_error_factory=lambda message: (
                FunctionNotWhitelistedError(message=message, span=span)
            ),
            blacklisted_error_factory=lambda message: FunctionBlacklistedError(
                message=message, span=span
            ),
        )
