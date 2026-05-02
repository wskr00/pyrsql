"""Shared query options."""

from dataclasses import dataclass
from dataclasses import field
from types import MappingProxyType
from typing import Any
from typing import Mapping
from typing import TypeVar

from pyrsql.core.conversion import DEFAULT_VALUE_CONVERTER_REGISTRY
from pyrsql.core.conversion import FieldValueConverterSet
from pyrsql.core.conversion import ValueConverter
from pyrsql.core.conversion import ValueConverterRegistry
from pyrsql.core.custom import CustomPredicateDefinition
from pyrsql.core.field_policy import FieldPolicySet
from pyrsql.core.json.options import JSONOptions
from pyrsql.core.joins import JoinHint
from pyrsql.parsing.limits import ParseLimits
from pyrsql.parsing.operators import DEFAULT_OPERATOR_REGISTRY
from pyrsql.parsing.operators import OperatorRegistry
from pyrsql.sorting.limits import SortLimits

_NestedValueT = TypeVar("_NestedValueT")


@dataclass(frozen=True, slots=True)
class QueryOptions:
    """Backend-neutral query options."""

    strict_equality: bool = False
    distinct: bool = False
    like_escape_character: str | None = None
    field_mapping: Mapping[str, str] = field(default_factory=dict)
    model_field_mapping: Mapping[type[Any], Mapping[str, str]] = field(
        default_factory=dict
    )
    join_hints: Mapping[str, JoinHint] = field(default_factory=dict)
    field_whitelist: frozenset[str] = field(default_factory=frozenset)
    field_blacklist: frozenset[str] = field(default_factory=frozenset)
    model_field_whitelist: Mapping[type[Any], frozenset[str]] = field(
        default_factory=dict
    )
    model_field_blacklist: Mapping[type[Any], frozenset[str]] = field(
        default_factory=dict
    )
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
    field_value_converters: Mapping[str, ValueConverter] = field(
        default_factory=dict
    )
    model_field_value_converters: Mapping[
        type[Any], Mapping[str, ValueConverter]
    ] = field(default_factory=dict)
    json_options: JSONOptions = field(default_factory=JSONOptions)

    def __post_init__(self) -> None:
        """Normalizes option containers into immutable representations."""
        object.__setattr__(
            self,
            "field_mapping",
            MappingProxyType(dict(self.field_mapping)),
        )
        object.__setattr__(
            self,
            "model_field_mapping",
            _normalize_nested_mapping(self.model_field_mapping),
        )
        object.__setattr__(
            self,
            "join_hints",
            MappingProxyType(dict(self.join_hints)),
        )
        object.__setattr__(
            self,
            "field_value_converters",
            MappingProxyType(dict(self.field_value_converters)),
        )
        object.__setattr__(
            self,
            "model_field_value_converters",
            _normalize_nested_mapping(self.model_field_value_converters),
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
            "model_field_whitelist",
            _normalize_nested_sets(self.model_field_whitelist),
        )
        object.__setattr__(
            self,
            "model_field_blacklist",
            _normalize_nested_sets(self.model_field_blacklist),
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

    @property
    def field_policy(self) -> FieldPolicySet:
        """Returns the normalized field mapping and access configuration."""
        return FieldPolicySet(
            field_mapping=self.field_mapping,
            field_whitelist=self.field_whitelist,
            field_blacklist=self.field_blacklist,
            model_field_mapping=self.model_field_mapping,
            model_field_whitelist=self.model_field_whitelist,
            model_field_blacklist=self.model_field_blacklist,
        )

    @property
    def field_converter_set(self) -> FieldValueConverterSet:
        """Returns the normalized field-scoped converter configuration."""
        return FieldValueConverterSet(
            field_converters=self.field_value_converters,
            model_field_converters=self.model_field_value_converters,
        )


@dataclass(frozen=True, slots=True)
class SortOptions:
    """Backend-neutral sort options."""

    field_mapping: Mapping[str, str] = field(default_factory=dict)
    model_field_mapping: Mapping[type[Any], Mapping[str, str]] = field(
        default_factory=dict
    )
    join_hints: Mapping[str, JoinHint] = field(default_factory=dict)
    field_whitelist: frozenset[str] = field(default_factory=frozenset)
    field_blacklist: frozenset[str] = field(default_factory=frozenset)
    model_field_whitelist: Mapping[type[Any], frozenset[str]] = field(
        default_factory=dict
    )
    model_field_blacklist: Mapping[type[Any], frozenset[str]] = field(
        default_factory=dict
    )
    procedure_whitelist: tuple[str, ...] = ()
    procedure_blacklist: tuple[str, ...] = ()
    sort_limits: SortLimits = field(default_factory=SortLimits)
    json_options: JSONOptions = field(default_factory=JSONOptions)

    def __post_init__(self) -> None:
        """Normalizes option containers into immutable representations."""
        object.__setattr__(
            self,
            "field_mapping",
            MappingProxyType(dict(self.field_mapping)),
        )
        object.__setattr__(
            self,
            "model_field_mapping",
            _normalize_nested_mapping(self.model_field_mapping),
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
            "model_field_whitelist",
            _normalize_nested_sets(self.model_field_whitelist),
        )
        object.__setattr__(
            self,
            "model_field_blacklist",
            _normalize_nested_sets(self.model_field_blacklist),
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

    @property
    def field_policy(self) -> FieldPolicySet:
        """Returns the normalized field mapping and access configuration."""
        return FieldPolicySet(
            field_mapping=self.field_mapping,
            field_whitelist=self.field_whitelist,
            field_blacklist=self.field_blacklist,
            model_field_mapping=self.model_field_mapping,
            model_field_whitelist=self.model_field_whitelist,
            model_field_blacklist=self.model_field_blacklist,
        )


def _normalize_nested_mapping(
    mapping: Mapping[type[Any], Mapping[str, _NestedValueT]],
) -> Mapping[type[Any], Mapping[str, _NestedValueT]]:
    """Normalizes nested mapping structures into immutable views."""
    return MappingProxyType(
        {
            model: MappingProxyType(dict(model_mapping))
            for model, model_mapping in mapping.items()
        }
    )


def _normalize_nested_sets(
    mapping: Mapping[type[Any], frozenset[str]],
) -> Mapping[type[Any], frozenset[str]]:
    """Normalizes nested set-like mappings into immutable views."""
    return MappingProxyType(
        {
            model: frozenset(values)
            for model, values in mapping.items()
        }
    )
