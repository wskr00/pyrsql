"""Supported comparison operators."""

from dataclasses import dataclass
from dataclasses import field
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True, slots=True)
class ComparisonOperator:
    """Represents a supported comparison operator."""

    name: str
    spellings: tuple[str, ...]
    minimum_arguments: int
    maximum_arguments: int | None

    def __post_init__(self) -> None:
        """Validates operator invariants."""
        if not self.name:
            raise ValueError("Operator name cannot be empty.")
        if not self.spellings:
            raise ValueError("Operator must define at least one spelling.")
        if self.minimum_arguments < 0:
            raise ValueError("minimum_arguments cannot be negative.")
        if (
            self.maximum_arguments is not None
            and self.maximum_arguments < self.minimum_arguments
        ):
            raise ValueError(
                "maximum_arguments cannot be less than minimum_arguments."
            )


@dataclass(frozen=True, slots=True)
class OperatorRegistry:
    """Immutable registry of supported comparison operators."""

    operators: tuple[ComparisonOperator, ...] = field(default_factory=tuple)
    operators_by_spelling: Mapping[str, ComparisonOperator] = field(
        init=False
    )
    operator_spellings: tuple[str, ...] = field(init=False)

    def __post_init__(self) -> None:
        """Builds lookup structures and validates uniqueness."""
        operators_by_spelling: dict[str, ComparisonOperator] = {}
        for operator in self.operators:
            for spelling in operator.spellings:
                if spelling in operators_by_spelling:
                    raise ValueError(
                        "Duplicate operator spelling registered: "
                        f"{spelling!r}."
                    )
                operators_by_spelling[spelling] = operator
        object.__setattr__(
            self,
            "operators_by_spelling",
            MappingProxyType(operators_by_spelling),
        )
        object.__setattr__(
            self,
            "operator_spellings",
            tuple(
                sorted(
                    operators_by_spelling,
                    key=len,
                    reverse=True,
                )
            ),
        )

    def get(self, spelling: str) -> ComparisonOperator:
        """Returns the operator registered for the provided spelling."""
        return self.operators_by_spelling[spelling]


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
    operators=SUPPORTED_COMPARISON_OPERATORS
)
OPERATOR_SPELLINGS = DEFAULT_OPERATOR_REGISTRY.operator_spellings
OPERATORS_BY_SPELLING = DEFAULT_OPERATOR_REGISTRY.operators_by_spelling
