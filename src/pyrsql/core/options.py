"""Shared query options."""

from dataclasses import dataclass
from dataclasses import field
from types import MappingProxyType
from typing import Mapping

from pyrsql.core.conversion import DEFAULT_VALUE_CONVERTER_REGISTRY
from pyrsql.core.conversion import ValueConverterRegistry
from pyrsql.core.custom import CustomPredicateDefinition
from pyrsql.core.joins import JoinHint
from pyrsql.parsing.limits import ParseLimits
from pyrsql.parsing.operators import DEFAULT_OPERATOR_REGISTRY
from pyrsql.parsing.operators import OperatorRegistry
from pyrsql.sorting.limits import SortLimits


@dataclass(frozen=True, slots=True)
class QueryOptions:
    """Backend-neutral query options."""

    strict_equality: bool = False
    distinct: bool = False
    like_escape_character: str | None = None
    field_mapping: Mapping[str, str] = field(default_factory=dict)
    join_hints: Mapping[str, JoinHint] = field(default_factory=dict)
    field_whitelist: frozenset[str] = field(default_factory=frozenset)
    field_blacklist: frozenset[str] = field(default_factory=frozenset)
    procedure_whitelist: tuple[str, ...] = ()
    procedure_blacklist: tuple[str, ...] = ()
    parse_limits: ParseLimits = field(default_factory=ParseLimits)
    operator_registry: OperatorRegistry = DEFAULT_OPERATOR_REGISTRY
    custom_predicates: Mapping[str, CustomPredicateDefinition] = field(
        default_factory=dict
    )
    value_converter_registry: ValueConverterRegistry = (
        DEFAULT_VALUE_CONVERTER_REGISTRY
    )

    def __post_init__(self) -> None:
        """Normalizes option containers into immutable representations."""
        object.__setattr__(
            self,
            "field_mapping",
            MappingProxyType(dict(self.field_mapping)),
        )
        object.__setattr__(
            self,
            "join_hints",
            MappingProxyType(dict(self.join_hints)),
        )
        object.__setattr__(
            self,
            "custom_predicates",
            MappingProxyType(dict(self.custom_predicates)),
        )
        object.__setattr__(
            self,
            "field_whitelist",
            frozenset(self.field_whitelist),
        )
        object.__setattr__(
            self,
            "field_blacklist",
            frozenset(self.field_blacklist),
        )
        object.__setattr__(
            self,
            "procedure_whitelist",
            tuple(self.procedure_whitelist),
        )
        object.__setattr__(
            self,
            "procedure_blacklist",
            tuple(self.procedure_blacklist),
        )
        object.__setattr__(
            self,
            "operator_registry",
            self._build_operator_registry(),
        )
        if (
            self.like_escape_character is not None
            and len(self.like_escape_character) != 1
        ):
            raise ValueError(
                "like_escape_character must be a single character when set."
            )

    def _build_operator_registry(self) -> OperatorRegistry:
        """Extends the configured operator registry with custom predicates."""
        if not self.custom_predicates:
            return self.operator_registry

        merged_operators = list(self.operator_registry.operators)
        operators_by_name = {
            operator.name: operator for operator in merged_operators
        }
        for operator_name, definition in self.custom_predicates.items():
            if definition.operator.name != operator_name:
                raise ValueError(
                    "custom_predicates keys must match their operator names."
                )
            existing_operator = operators_by_name.get(operator_name)
            if existing_operator is None:
                merged_operators.append(definition.operator)
                operators_by_name[operator_name] = definition.operator
                continue
            if existing_operator != definition.operator:
                raise ValueError(
                    "custom_predicates cannot redefine an existing "
                    f"operator differently: {operator_name!r}."
                )
        return OperatorRegistry(operators=tuple(merged_operators))


@dataclass(frozen=True, slots=True)
class SortOptions:
    """Backend-neutral sort options."""

    field_mapping: Mapping[str, str] = field(default_factory=dict)
    join_hints: Mapping[str, JoinHint] = field(default_factory=dict)
    field_whitelist: frozenset[str] = field(default_factory=frozenset)
    field_blacklist: frozenset[str] = field(default_factory=frozenset)
    procedure_whitelist: tuple[str, ...] = ()
    procedure_blacklist: tuple[str, ...] = ()
    sort_limits: SortLimits = field(default_factory=SortLimits)

    def __post_init__(self) -> None:
        """Normalizes option containers into immutable representations."""
        object.__setattr__(
            self,
            "field_mapping",
            MappingProxyType(dict(self.field_mapping)),
        )
        object.__setattr__(
            self,
            "join_hints",
            MappingProxyType(dict(self.join_hints)),
        )
        object.__setattr__(
            self,
            "field_whitelist",
            frozenset(self.field_whitelist),
        )
        object.__setattr__(
            self,
            "field_blacklist",
            frozenset(self.field_blacklist),
        )
        object.__setattr__(
            self,
            "procedure_whitelist",
            tuple(self.procedure_whitelist),
        )
        object.__setattr__(
            self,
            "procedure_blacklist",
            tuple(self.procedure_blacklist),
        )
