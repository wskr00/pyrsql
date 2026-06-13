"""Supported comparison operators."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

import msgspec

if TYPE_CHECKING:
    from collections.abc import Mapping


def _validate_non_empty_string(value: str, *, field_name: str) -> None:
    """Validates one required non-empty string field.

    Raises:
        TypeError: If the field is not a string.
        ValueError: If the field is empty or padded with outer whitespace.
    """
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string.")
    if not value:
        raise ValueError(f"{field_name} cannot be empty.")
    if value != value.strip():
        raise ValueError(
            f"{field_name} must not contain outer whitespace.",
        )


def _validate_non_negative_int(value: int, *, field_name: str) -> None:
    """Validates one non-negative integer field.

    Raises:
        TypeError: If the field is not an integer.
        ValueError: If the field is negative.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer.")
    if value < 0:
        raise ValueError(f"{field_name} cannot be negative.")


class ComparisonOperator(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Represents a supported comparison operator."""

    name: str
    spellings: tuple[str, ...]
    minimum_arguments: int
    maximum_arguments: int | None

    def __post_init__(self) -> None:
        """Validates operator invariants.

        Raises:
            TypeError: If the operator definition uses invalid runtime types.
            ValueError: If the operator definition is invalid.
        """
        _validate_non_empty_string(self.name, field_name="name")
        if isinstance(self.spellings, str) or not isinstance(
            self.spellings,
            tuple,
        ):
            raise TypeError("spellings must be a tuple of strings.")
        if not self.spellings:
            raise ValueError("Operator must define at least one spelling.")
        for spelling in self.spellings:
            _validate_non_empty_string(
                spelling,
                field_name="operator spelling",
            )
        if len(set(self.spellings)) != len(self.spellings):
            raise ValueError("Operator spellings must be unique.")
        _validate_non_negative_int(
            self.minimum_arguments,
            field_name="minimum_arguments",
        )
        if self.maximum_arguments is not None:
            _validate_non_negative_int(
                self.maximum_arguments,
                field_name="maximum_arguments",
            )
        if (
            self.maximum_arguments is not None
            and self.maximum_arguments < self.minimum_arguments
        ):
            raise ValueError(
                "maximum_arguments cannot be less than minimum_arguments.",
            )


class OperatorRegistry(msgspec.Struct, frozen=True, gc=False):
    """Immutable registry of supported comparison operators."""

    operators: tuple[ComparisonOperator, ...] = ()
    _operators_by_spelling: Mapping[str, ComparisonOperator] = MappingProxyType(
        {}
    )
    _operator_spellings_by_prefix: Mapping[str, tuple[str, ...]] = (
        MappingProxyType({})
    )

    def __post_init__(self) -> None:
        """Builds lookup structures and validates uniqueness.

        Raises:
            TypeError: If the registered operators do not match the runtime
                contract.
            ValueError: If no operators are registered or spellings collide.
        """
        if isinstance(self.operators, str) or not isinstance(
            self.operators,
            tuple,
        ):
            raise TypeError("operators must be a tuple of ComparisonOperator.")
        if not self.operators:
            raise ValueError("Operator registry must contain operators.")
        for operator in self.operators:
            if not isinstance(operator, ComparisonOperator):
                raise TypeError(
                    "operators must contain only ComparisonOperator instances.",
                )
        operators_by_spelling: dict[str, ComparisonOperator] = {}
        spellings_by_prefix: dict[str, list[str]] = {}
        for operator in self.operators:
            for spelling in operator.spellings:
                if spelling in operators_by_spelling:
                    raise ValueError(
                        f"Duplicate operator spelling registered: {spelling!r}.",  # noqa: E501
                    )
                operators_by_spelling[spelling] = operator
                spellings_by_prefix.setdefault(spelling[0], []).append(spelling)
        msgspec.structs.force_setattr(
            self,
            "_operators_by_spelling",
            MappingProxyType(operators_by_spelling),
        )
        msgspec.structs.force_setattr(
            self,
            "_operator_spellings_by_prefix",
            MappingProxyType(
                {
                    prefix: tuple(sorted(spellings, key=len, reverse=True))
                    for prefix, spellings in spellings_by_prefix.items()
                },
            ),
        )

    def get(self, spelling: str) -> ComparisonOperator:
        """Returns the operator registered for the provided spelling.

        Returns:
            The registered comparison operator.
        """
        return self._operators_by_spelling[spelling]

    def match_candidates(self, prefix: str) -> tuple[str, ...]:
        """Returns operator spellings that can start with the prefix.

        Returns:
            Candidate operator spellings for the prefix.
        """
        return self._operator_spellings_by_prefix.get(prefix, ())


EQUAL = ComparisonOperator(
    name="equal",
    spellings=("==",),
    minimum_arguments=1,
    maximum_arguments=1,
)
NOT_EQUAL = ComparisonOperator(
    name="not_equal",
    spellings=("!=",),
    minimum_arguments=1,
    maximum_arguments=1,
)
GREATER_THAN = ComparisonOperator(
    name="greater_than",
    spellings=("=gt=", ">"),
    minimum_arguments=1,
    maximum_arguments=1,
)
GREATER_THAN_OR_EQUAL = ComparisonOperator(
    name="greater_than_or_equal",
    spellings=("=ge=", ">="),
    minimum_arguments=1,
    maximum_arguments=1,
)
LESS_THAN = ComparisonOperator(
    name="less_than",
    spellings=("=lt=", "<"),
    minimum_arguments=1,
    maximum_arguments=1,
)
LESS_THAN_OR_EQUAL = ComparisonOperator(
    name="less_than_or_equal",
    spellings=("=le=", "<="),
    minimum_arguments=1,
    maximum_arguments=1,
)
IN = ComparisonOperator(
    name="in",
    spellings=("=in=",),
    minimum_arguments=1,
    maximum_arguments=None,
)
NOT_IN = ComparisonOperator(
    name="not_in",
    spellings=("=out=",),
    minimum_arguments=1,
    maximum_arguments=None,
)
IS_NULL = ComparisonOperator(
    name="is_null",
    spellings=("=na=", "=isnull=", "=null="),
    minimum_arguments=0,
    maximum_arguments=1,
)
NOT_NULL = ComparisonOperator(
    name="not_null",
    spellings=("=nn=", "=notnull=", "=isnotnull="),
    minimum_arguments=0,
    maximum_arguments=1,
)
LIKE = ComparisonOperator(
    name="like",
    spellings=("=like=", "=ke="),
    minimum_arguments=1,
    maximum_arguments=1,
)
NOT_LIKE = ComparisonOperator(
    name="not_like",
    spellings=("=notlike=", "=nk="),
    minimum_arguments=1,
    maximum_arguments=1,
)
IGNORE_CASE = ComparisonOperator(
    name="ignore_case",
    spellings=("=ic=", "=icase="),
    minimum_arguments=1,
    maximum_arguments=1,
)
IGNORE_CASE_LIKE = ComparisonOperator(
    name="ignore_case_like",
    spellings=("=ilike=", "=ik="),
    minimum_arguments=1,
    maximum_arguments=1,
)
IGNORE_CASE_NOT_LIKE = ComparisonOperator(
    name="ignore_case_not_like",
    spellings=("=inotlike=", "=ni="),
    minimum_arguments=1,
    maximum_arguments=1,
)
BETWEEN = ComparisonOperator(
    name="between",
    spellings=("=bt=", "=between="),
    minimum_arguments=2,
    maximum_arguments=2,
)
NOT_BETWEEN = ComparisonOperator(
    name="not_between",
    spellings=("=nb=", "=notbetween="),
    minimum_arguments=2,
    maximum_arguments=2,
)

SUPPORTED_COMPARISON_OPERATORS = (
    EQUAL,
    NOT_EQUAL,
    GREATER_THAN,
    GREATER_THAN_OR_EQUAL,
    LESS_THAN,
    LESS_THAN_OR_EQUAL,
    IN,
    NOT_IN,
    IS_NULL,
    NOT_NULL,
    LIKE,
    NOT_LIKE,
    IGNORE_CASE,
    IGNORE_CASE_LIKE,
    IGNORE_CASE_NOT_LIKE,
    BETWEEN,
    NOT_BETWEEN,
)

DEFAULT_OPERATOR_REGISTRY = OperatorRegistry(
    operators=SUPPORTED_COMPARISON_OPERATORS,
)
