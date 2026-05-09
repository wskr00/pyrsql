"""ORM-neutral semantic binder."""

from collections.abc import Callable, Mapping
from typing import Protocol

from pyrsql.ir.query import (
    BoundArgument,
    BoundComparison,
    BoundField,
    BoundFunction,
    BoundLiteral,
    BoundLogical,
    BoundSelectorNode,
)
from pyrsql.parsing.ast import ComparisonNode, Expression, LogicalNode
from pyrsql.parsing.source import SourceSpan
from pyrsql.selector.ast import (
    FieldSelector,
    FunctionSelector,
    LiteralSelector,
    SelectorNode,
)
from pyrsql.semantic.errors import (
    FieldBlacklistedError,
    FieldNotWhitelistedError,
    FunctionBlacklistedError,
    FunctionNotWhitelistedError,
)


class ProcedurePolicyProtocol(Protocol):
    """Structural contract for procedure access policies."""

    def is_whitelisted(self, function_name: str) -> bool:
        """Returns whether the function is allowed by the whitelist."""

    def is_blacklisted(self, function_name: str) -> bool:
        """Returns whether the function is blocked by the blacklist."""


class SemanticBindingOptions(Protocol):
    """Structural options contract required by the semantic binder."""

    @property
    def field_mapping(self) -> Mapping[str, str]:
        """Field mapping available to the binder."""

    @property
    def field_whitelist(self) -> frozenset[str] | set[str]:
        """Field whitelist available to the binder."""

    @property
    def field_blacklist(self) -> frozenset[str] | set[str]:
        """Field blacklist available to the binder."""

    @property
    def procedure_policy(self) -> ProcedurePolicyProtocol:
        """Procedure access policy available to the binder."""


class SemanticBinder:
    """Binds parsed query AST nodes into logical IR."""

    def __init__(self, options: SemanticBindingOptions) -> None:
        """Initializes the binder with semantic binding options."""
        self._field_whitelist = options.field_whitelist
        self._field_blacklist = options.field_blacklist
        self._procedure_policy = options.procedure_policy
        self._field_mapping = options.field_mapping

    def bind(self, expression: Expression) -> BoundComparison | BoundLogical:
        """Binds a parsed AST into a bound logical expression tree.

        Returns:
            The bound logical expression tree.

        Raises:
            TypeError: If the expression is not a supported AST node.
        """
        if isinstance(expression, ComparisonNode):
            return self._bind_comparison(expression)
        if not isinstance(expression, LogicalNode):
            raise TypeError("Expected LogicalNode")
        return BoundLogical(
            span=expression.span,
            operator=expression.operator,
            children=tuple(self.bind(child) for child in expression.children),
        )

    def _bind_comparison(
        self,
        expression: ComparisonNode,
    ) -> BoundComparison:
        """Binds a parsed comparison node.

        Returns:
            The bound comparison node.
        """
        return BoundComparison(
            span=expression.span,
            selector=self._bind_selector(
                expression.selector,
                span=expression.span,
            ),
            operator=expression.operator,
            arguments=tuple(
                BoundArgument(
                    text=argument.text,
                    quoted=argument.quoted,
                    span=argument.span,
                )
                for argument in expression.arguments
            ),
        )

    def _bind_selector(
        self,
        selector: SelectorNode,
        *,
        span: SourceSpan,
    ) -> BoundSelectorNode:
        """Binds a parsed selector recursively.

        Returns:
            The bound selector node.
        """
        return _bind_selector(
            selector,
            field_mapping=self._field_mapping,
            validate_field=lambda field_path: self._enforce_field_access_policy(
                field_path,
                span,
            ),
            validate_function=(
                lambda function_name: self._enforce_function_access_policy(
                    function_name,
                    span=span,
                )
            ),
        )

    def _enforce_field_access_policy(
        self,
        field_path: str,
        span: SourceSpan,
    ) -> None:
        """Validates whitelist and blacklist rules.

        Raises:
            FieldNotWhitelistedError: If the field is not allowed.
            FieldBlacklistedError: If the field is blocked.
        """
        if self._field_whitelist and field_path not in self._field_whitelist:
            raise FieldNotWhitelistedError(
                message=f"Field {field_path!r} is not allowed",
                span=span,
            )
        if field_path in self._field_blacklist:
            raise FieldBlacklistedError(
                message=f"Field {field_path!r} is blocked",
                span=span,
            )

    def _enforce_function_access_policy(
        self,
        function_name: str,
        *,
        span: SourceSpan,
    ) -> None:
        """Validates whitelist and blacklist rules for functions.

        Raises:
            FunctionNotWhitelistedError: If the function is not allowed.
            FunctionBlacklistedError: If the function is blocked.
        """
        if not self._procedure_policy.is_whitelisted(function_name):
            raise FunctionNotWhitelistedError(
                message=f"Function {function_name!r} is not whitelisted",
                span=span,
            )
        if self._procedure_policy.is_blacklisted(function_name):
            raise FunctionBlacklistedError(
                message=f"Function {function_name!r} is blacklisted",
                span=span,
            )


def _bind_selector(
    selector: SelectorNode,
    *,
    field_mapping: Mapping[str, str],
    validate_field: Callable[[str], None],
    validate_function: Callable[[str], None],
) -> BoundSelectorNode:
    """Binds one parsed selector recursively.

    Returns:
        The bound selector node.

    Raises:
        TypeError: If the selector is not a supported selector node.
    """
    if isinstance(selector, FieldSelector):
        field_path = field_mapping.get(selector.raw_path, selector.raw_path)
        validate_field(field_path)
        return BoundField(
            raw_path=selector.raw_path,
            field_path=field_path,
            segments=tuple(field_path.split(".")),
        )
    if isinstance(selector, LiteralSelector):
        return BoundLiteral(value=selector.value)
    if not isinstance(selector, FunctionSelector):
        raise TypeError("Expected FunctionSelector")
    validate_function(selector.function_name)
    return BoundFunction(
        function_name=selector.function_name,
        arguments=tuple(
            _bind_selector(
                argument,
                field_mapping=field_mapping,
                validate_field=validate_field,
                validate_function=validate_function,
            )
            for argument in selector.arguments
        ),
    )
