"""ORM-neutral binder for parsed sort fields."""

from collections.abc import Callable, Mapping
from typing import Protocol

from pyrsql.ir.query import (
    BoundField,
    BoundFunction,
    BoundLiteral,
    BoundSelectorNode,
)
from pyrsql.ir.sort import BoundSort, BoundSortField
from pyrsql.selector.ast import (
    FieldSelector,
    FunctionSelector,
    LiteralSelector,
    SelectorNode,
)
from pyrsql.sorting.ast import SortField
from pyrsql.sorting.errors import (
    SortFieldBlacklistedError,
    SortFieldNotWhitelistedError,
    SortFunctionBlacklistedError,
    SortFunctionNotWhitelistedError,
)


class ProcedurePolicyProtocol(Protocol):
    """Structural contract for procedure access policies."""

    def is_whitelisted(self, function_name: str) -> bool:
        """Returns whether the function is allowed by the whitelist."""

    def is_blacklisted(self, function_name: str) -> bool:
        """Returns whether the function is blocked by the blacklist."""


class SortBindingOptions(Protocol):
    """Structural options contract required by the sort binder."""

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


class SortBinder:
    """Binds parsed sort fields into logical sort IR."""

    def __init__(self, options: SortBindingOptions) -> None:
        """Initializes the binder with sort binding options."""
        self._field_whitelist = options.field_whitelist
        self._field_blacklist = options.field_blacklist
        self._procedure_policy = options.procedure_policy
        self._field_mapping = options.field_mapping

    def bind(self, fields: tuple[SortField, ...]) -> BoundSort:
        """Binds parsed sort fields into a bound sort request.

        Returns:
            A bound sort request.
        """
        return BoundSort(
            fields=tuple(self._bind_field(field) for field in fields),
        )

    def _bind_field(self, field: SortField) -> BoundSortField:
        """Binds a single parsed sort field.

        Returns:
            The bound sort field.
        """
        return BoundSortField(
            selector=self._bind_selector(field.selector),
            direction=field.direction,
            ignore_case=field.ignore_case,
        )

    def _bind_selector(self, selector: SelectorNode) -> BoundSelectorNode:
        """Binds a parsed selector recursively.

        Returns:
            The bound selector node.
        """
        return _bind_selector(
            selector,
            field_mapping=self._field_mapping,
            validate_field=self._enforce_field_access_policy,
            validate_function=self._enforce_function_access_policy,
        )

    def _enforce_field_access_policy(self, field_path: str) -> None:
        """Validates whitelist and blacklist rules.

        Raises:
            SortFieldNotWhitelistedError: If the field is not allowed.
            SortFieldBlacklistedError: If the field is blocked.
        """
        if self._field_whitelist and field_path not in self._field_whitelist:
            raise SortFieldNotWhitelistedError(
                message=f"Field {field_path!r} is not allowed",
            )
        if field_path in self._field_blacklist:
            raise SortFieldBlacklistedError(
                message=f"Field {field_path!r} is blocked",
            )

    def _enforce_function_access_policy(self, function_name: str) -> None:
        """Validates whitelist and blacklist rules for functions.

        Raises:
            SortFunctionNotWhitelistedError: If the function is not allowed.
            SortFunctionBlacklistedError: If the function is blocked.
        """
        if not self._procedure_policy.is_whitelisted(function_name):
            raise SortFunctionNotWhitelistedError(
                message=f"Function {function_name!r} is not whitelisted",
            )
        if self._procedure_policy.is_blacklisted(function_name):
            raise SortFunctionBlacklistedError(
                message=f"Function {function_name!r} is blacklisted",
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
