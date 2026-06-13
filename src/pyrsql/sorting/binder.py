"""ORM-neutral binder for parsed sort fields."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrsql.core.binding_policy import (
    MappedFieldBindingOptions,
    enforce_field_access_policy,
    enforce_function_access_policy,
)
from pyrsql.selector.ast import (
    FieldSelector,
    FunctionSelector,
    LiteralSelector,
)
from pyrsql.sorting.ast import SortField
from pyrsql.sorting.errors import (
    SortFieldBlacklistedError,
    SortFieldNotWhitelistedError,
    SortFunctionBlacklistedError,
    SortFunctionNotWhitelistedError,
)

if TYPE_CHECKING:
    from pyrsql.selector.ast import (
        SelectorNode,
    )


class SortBinder:
    """Normalizes parsed sort fields after semantic checks."""

    def __init__(self, options: MappedFieldBindingOptions) -> None:
        """Initializes the binder with sort binding options."""
        self._field_whitelist = options.field_whitelist
        self._field_blacklist = options.field_blacklist
        self._procedure_policy = options.procedure_policy
        self._field_mapping = options.field_mapping

    def bind(self, fields: tuple[SortField, ...]) -> tuple[SortField, ...]:
        """Normalizes parsed sort fields after semantic validation.

        Returns:
            Semantically validated sort fields.
        """
        return tuple(self._bind_field(field) for field in fields)

    def _bind_field(self, field: SortField) -> SortField:
        """Normalizes a single parsed sort field.

        Returns:
            The semantically validated sort field.
        """
        return SortField(
            selector=self._bind_selector(field.selector),
            direction=field.direction,
            ignore_case=field.ignore_case,
        )

    def _bind_selector(self, selector: SelectorNode) -> SelectorNode:
        """Normalizes a parsed selector recursively.

        Returns:
            The semantically validated selector node.

        Raises:
            TypeError: If the selector is not a supported selector node.
        """
        if isinstance(selector, FieldSelector):
            field_path = self._field_mapping.get(
                selector.raw_path,
                selector.raw_path,
            )
            self._enforce_field_access_policy(field_path)
            return FieldSelector(
                raw_path=field_path,
            )
        if isinstance(selector, LiteralSelector):
            return selector
        if not isinstance(selector, FunctionSelector):
            raise TypeError(
                "Expected FieldSelector, LiteralSelector, or FunctionSelector.",
            )
        self._enforce_function_access_policy(selector.function_name)
        return FunctionSelector(
            function_name=selector.function_name,
            arguments=tuple(
                self._bind_selector(argument) for argument in selector.arguments
            ),
        )

    def _enforce_field_access_policy(self, field_path: str) -> None:
        """Validates whitelist and blacklist rules."""
        enforce_field_access_policy(
            field_path,
            field_whitelist=self._field_whitelist,
            field_blacklist=self._field_blacklist,
            not_whitelisted_error_factory=lambda message: (
                SortFieldNotWhitelistedError(message=message)
            ),
            blacklisted_error_factory=lambda message: SortFieldBlacklistedError(
                message=message
            ),
        )

    def _enforce_function_access_policy(self, function_name: str) -> None:
        """Validates whitelist and blacklist rules for functions."""
        enforce_function_access_policy(
            function_name,
            procedure_policy=self._procedure_policy,
            not_whitelisted_error_factory=lambda message: (
                SortFunctionNotWhitelistedError(message=message)
            ),
            blacklisted_error_factory=lambda message: (
                SortFunctionBlacklistedError(message=message)
            ),
        )
