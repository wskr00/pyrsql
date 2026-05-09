"""Shared query options."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Final, Protocol, TypeVar

from pyrsql.core.conversion import (
    DEFAULT_FIELD_VALUE_CONVERTER_SET,
    DEFAULT_VALUE_CONVERTER_REGISTRY,
    FieldValueConverterSet,
    ValueConverter,
    ValueConverterRegistry,
)
from pyrsql.core.custom import CustomPredicateDefinition
from pyrsql.core.field_policy import DEFAULT_FIELD_POLICY_SET, FieldPolicySet
from pyrsql.core.joins import JoinHint
from pyrsql.core.json.options import DEFAULT_JSON_OPTIONS, JSONOptions
from pyrsql.core.procedure_policy import (
    DEFAULT_PROCEDURE_ACCESS_POLICY,
    ProcedureAccessPolicy,
)
from pyrsql.parsing.limits import DEFAULT_PARSE_LIMITS, ParseLimits
from pyrsql.parsing.operators import DEFAULT_OPERATOR_REGISTRY, OperatorRegistry
from pyrsql.sorting.limits import DEFAULT_SORT_LIMITS, SortLimits

_NestedValueT = TypeVar("_NestedValueT")
_EMPTY_TUPLE: Final[tuple[str, ...]] = ()


class _SharedPolicyOptionsProtocol(Protocol):
    """Structural contract for shared field/procedure policy options."""

    @property
    def field_mapping(self) -> Mapping[str, str]: ...

    @property
    def model_field_mapping(
        self,
    ) -> Mapping[type[Any], Mapping[str, str]]: ...

    @property
    def join_hints(self) -> Mapping[str, JoinHint]: ...

    @property
    def field_whitelist(self) -> frozenset[str]: ...

    @property
    def field_blacklist(self) -> frozenset[str]: ...

    @property
    def model_field_whitelist(
        self,
    ) -> Mapping[type[Any], frozenset[str]]: ...

    @property
    def model_field_blacklist(
        self,
    ) -> Mapping[type[Any], frozenset[str]]: ...

    @property
    def procedure_whitelist(self) -> tuple[str, ...]: ...

    @property
    def procedure_blacklist(self) -> tuple[str, ...]: ...


def _normalize_mapping(
    mapping: Mapping[str, _NestedValueT],
) -> Mapping[str, _NestedValueT]:
    """Normalizes a flat mapping into an immutable view.

    Returns:
        An immutable copy of the provided mapping.
    """
    return MappingProxyType(dict(mapping))


def _normalize_tuple(values: tuple[str, ...]) -> tuple[str, ...]:
    """Normalizes tuple-like string containers.

    Returns:
        An immutable tuple copy of the provided values.
    """
    return tuple(values)


def _normalize_frozenset(values: frozenset[str]) -> frozenset[str]:
    """Normalizes set-like string containers.

    Returns:
        An immutable frozenset copy of the provided values.
    """
    return frozenset(values)


def _normalize_shared_policy_options(
    options: _SharedPolicyOptionsProtocol,
) -> None:
    """Normalizes option fields shared by query and sort configuration."""
    object.__setattr__(
        options,
        "field_mapping",
        _normalize_mapping(options.field_mapping),
    )
    object.__setattr__(
        options,
        "model_field_mapping",
        _normalize_nested_mapping(options.model_field_mapping),
    )
    object.__setattr__(
        options,
        "join_hints",
        _normalize_mapping(options.join_hints),
    )
    object.__setattr__(
        options,
        "field_whitelist",
        _normalize_frozenset(options.field_whitelist),
    )
    object.__setattr__(
        options,
        "field_blacklist",
        _normalize_frozenset(options.field_blacklist),
    )
    object.__setattr__(
        options,
        "model_field_whitelist",
        _normalize_nested_sets(options.model_field_whitelist),
    )
    object.__setattr__(
        options,
        "model_field_blacklist",
        _normalize_nested_sets(options.model_field_blacklist),
    )
    object.__setattr__(
        options,
        "procedure_whitelist",
        _normalize_tuple(options.procedure_whitelist),
    )
    object.__setattr__(
        options,
        "procedure_blacklist",
        _normalize_tuple(options.procedure_blacklist),
    )


def _validate_like_escape_character(
    like_escape_character: str | None,
) -> None:
    """Validates one optional SQL LIKE escape character.

    Raises:
        ValueError: If the configured escape character is not exactly one
            character long.
    """
    if like_escape_character is not None and len(like_escape_character) != 1:
        raise ValueError(
            "like_escape_character must be a single character when set.",
        )


def _build_field_policy(
    *,
    field_mapping: Mapping[str, str],
    field_whitelist: frozenset[str],
    field_blacklist: frozenset[str],
    model_field_mapping: Mapping[type[Any], Mapping[str, str]],
    model_field_whitelist: Mapping[type[Any], frozenset[str]],
    model_field_blacklist: Mapping[type[Any], frozenset[str]],
) -> FieldPolicySet:
    """Builds a normalized field policy from option values.

    Returns:
        A compiled field policy object.
    """
    return FieldPolicySet(
        field_mapping=field_mapping,
        field_whitelist=field_whitelist,
        field_blacklist=field_blacklist,
        model_field_mapping=model_field_mapping,
        model_field_whitelist=model_field_whitelist,
        model_field_blacklist=model_field_blacklist,
    )


def _build_procedure_policy(
    whitelist: tuple[str, ...],
    blacklist: tuple[str, ...],
) -> ProcedureAccessPolicy:
    """Builds a compiled procedure policy from raw patterns.

    Returns:
        A compiled procedure access policy.
    """
    return ProcedureAccessPolicy.from_patterns(whitelist, blacklist)


@dataclass(frozen=True, slots=True)
class QueryOptions:
    """ORM-neutral configuration for parsing and compiling queries.

    The options bundle parser limits, operator registries, field policies,
    custom predicates, value converters, and JSON behavior in one immutable
    object.
    """

    strict_equality: bool = False
    distinct: bool = False
    like_escape_character: str | None = None
    field_mapping: Mapping[str, str] = field(default_factory=dict)
    model_field_mapping: Mapping[type[Any], Mapping[str, str]] = field(
        default_factory=dict,
    )
    join_hints: Mapping[str, JoinHint] = field(default_factory=dict)
    field_whitelist: frozenset[str] = field(default_factory=frozenset)
    field_blacklist: frozenset[str] = field(default_factory=frozenset)
    model_field_whitelist: Mapping[type[Any], frozenset[str]] = field(
        default_factory=dict,
    )
    model_field_blacklist: Mapping[type[Any], frozenset[str]] = field(
        default_factory=dict,
    )
    procedure_whitelist: tuple[str, ...] = ()
    procedure_blacklist: tuple[str, ...] = ()
    parse_limits: ParseLimits = DEFAULT_PARSE_LIMITS
    operator_registry: OperatorRegistry = DEFAULT_OPERATOR_REGISTRY
    custom_predicates: Mapping[str, CustomPredicateDefinition] = field(
        default_factory=dict,
    )
    value_converter_registry: ValueConverterRegistry = (
        DEFAULT_VALUE_CONVERTER_REGISTRY
    )
    field_value_converters: Mapping[str, ValueConverter] = field(
        default_factory=dict,
    )
    model_field_value_converters: Mapping[
        type[Any], Mapping[str, ValueConverter],
    ] = field(default_factory=dict)
    json_options: JSONOptions = DEFAULT_JSON_OPTIONS
    _field_policy: FieldPolicySet = field(
        init=False,
        repr=False,
        compare=False,
    )
    _field_converter_set: FieldValueConverterSet = field(
        init=False,
        repr=False,
        compare=False,
    )
    _procedure_policy: ProcedureAccessPolicy = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        """Normalizes option containers into immutable representations."""
        _normalize_shared_policy_options(self)
        object.__setattr__(
            self,
            "field_value_converters",
            _normalize_mapping(self.field_value_converters),
        )
        object.__setattr__(
            self,
            "model_field_value_converters",
            _normalize_nested_mapping(self.model_field_value_converters),
        )
        object.__setattr__(
            self,
            "custom_predicates",
            _normalize_mapping(self.custom_predicates),
        )
        object.__setattr__(
            self,
            "operator_registry",
            self._build_operator_registry(),
        )
        _validate_like_escape_character(self.like_escape_character)
        object.__setattr__(self, "_field_policy", self._build_field_policy())
        object.__setattr__(
            self,
            "_field_converter_set",
            self._build_field_converter_set(),
        )
        object.__setattr__(
            self,
            "_procedure_policy",
            self._build_procedure_policy(),
        )

    def _build_operator_registry(self) -> OperatorRegistry:
        """Extends the configured operator registry with custom predicates.

        Returns:
            The configured operator registry, extended with custom predicates.

        Raises:
            ValueError: If a custom predicate key does not match its operator
                name, or if it attempts to redefine an existing operator with a
                different definition.
        """
        if not self.custom_predicates:
            return self.operator_registry

        merged_operators = list(self.operator_registry.operators)
        operators_by_name = {
            operator.name: operator for operator in merged_operators
        }
        for operator_name, definition in self.custom_predicates.items():
            if definition.operator.name != operator_name:
                raise ValueError(
                    "custom_predicates keys must match their operator names.",
                )
            existing_operator = operators_by_name.get(operator_name)
            if existing_operator is None:
                merged_operators.append(definition.operator)
                operators_by_name[operator_name] = definition.operator
                continue
            if existing_operator != definition.operator:
                raise ValueError(
                    "custom_predicates cannot redefine an existing "
                    f"operator differently: {operator_name!r}.",
                )
        return OperatorRegistry(operators=tuple(merged_operators))

    @property
    def field_policy(self) -> FieldPolicySet:
        """The normalized field mapping and access configuration.

        Returns:
            The compiled field policy for this query configuration.
        """
        return self._field_policy

    @property
    def field_converter_set(self) -> FieldValueConverterSet:
        """The normalized field-scoped converter configuration.

        Returns:
            The compiled field converter set for this query configuration.
        """
        return self._field_converter_set

    @property
    def procedure_policy(self) -> ProcedureAccessPolicy:
        """The compiled procedure access policy.

        Returns:
            The compiled procedure access policy for this query configuration.
        """
        return self._procedure_policy

    def _build_field_policy(self) -> FieldPolicySet:
        """Builds the immutable field-policy object once.

        Returns:
            The normalized field policy for this query configuration.
        """
        if not any(
            (
                self.field_mapping,
                self.field_whitelist,
                self.field_blacklist,
                self.model_field_mapping,
                self.model_field_whitelist,
                self.model_field_blacklist,
            ),
        ):
            return DEFAULT_FIELD_POLICY_SET
        return _build_field_policy(
            field_mapping=self.field_mapping,
            field_whitelist=self.field_whitelist,
            field_blacklist=self.field_blacklist,
            model_field_mapping=self.model_field_mapping,
            model_field_whitelist=self.model_field_whitelist,
            model_field_blacklist=self.model_field_blacklist,
        )

    def _build_field_converter_set(self) -> FieldValueConverterSet:
        """Builds the immutable field-converter object once.

        Returns:
            The normalized field-scoped converter set.
        """
        if (
            not self.field_value_converters
            and not self.model_field_value_converters
        ):
            return DEFAULT_FIELD_VALUE_CONVERTER_SET
        return FieldValueConverterSet(
            field_converters=self.field_value_converters,
            model_field_converters=self.model_field_value_converters,
        )

    def _build_procedure_policy(self) -> ProcedureAccessPolicy:
        """Builds the compiled procedure policy once.

        Returns:
            The compiled procedure access policy for this query configuration.
        """
        if not self.procedure_whitelist and not self.procedure_blacklist:
            return DEFAULT_PROCEDURE_ACCESS_POLICY
        return _build_procedure_policy(
            self.procedure_whitelist,
            self.procedure_blacklist,
        )


@dataclass(frozen=True, slots=True)
class SortOptions:
    """ORM-neutral sort options."""

    field_mapping: Mapping[str, str] = field(default_factory=dict)
    model_field_mapping: Mapping[type[Any], Mapping[str, str]] = field(
        default_factory=dict,
    )
    join_hints: Mapping[str, JoinHint] = field(default_factory=dict)
    field_whitelist: frozenset[str] = field(default_factory=frozenset)
    field_blacklist: frozenset[str] = field(default_factory=frozenset)
    model_field_whitelist: Mapping[type[Any], frozenset[str]] = field(
        default_factory=dict,
    )
    model_field_blacklist: Mapping[type[Any], frozenset[str]] = field(
        default_factory=dict,
    )
    procedure_whitelist: tuple[str, ...] = ()
    procedure_blacklist: tuple[str, ...] = ()
    sort_limits: SortLimits = DEFAULT_SORT_LIMITS
    json_options: JSONOptions = DEFAULT_JSON_OPTIONS
    _field_policy: FieldPolicySet = field(
        init=False,
        repr=False,
        compare=False,
    )
    _procedure_policy: ProcedureAccessPolicy = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        """Normalizes option containers into immutable representations."""
        _normalize_shared_policy_options(self)
        object.__setattr__(self, "_field_policy", self._build_field_policy())
        object.__setattr__(
            self,
            "_procedure_policy",
            self._build_procedure_policy(),
        )

    @property
    def field_policy(self) -> FieldPolicySet:
        """Returns the normalized field mapping and access configuration.

        Returns:
            The compiled field policy for this sort configuration.
        """
        return self._field_policy

    @property
    def procedure_policy(self) -> ProcedureAccessPolicy:
        """Returns the compiled procedure access policy.

        Returns:
            The compiled procedure access policy for this sort configuration.
        """
        return self._procedure_policy

    def _build_field_policy(self) -> FieldPolicySet:
        """Builds the immutable field-policy object once.

        Returns:
            The normalized field policy for this sort configuration.
        """
        if not any(
            (
                self.field_mapping,
                self.field_whitelist,
                self.field_blacklist,
                self.model_field_mapping,
                self.model_field_whitelist,
                self.model_field_blacklist,
            ),
        ):
            return DEFAULT_FIELD_POLICY_SET
        return _build_field_policy(
            field_mapping=self.field_mapping,
            field_whitelist=self.field_whitelist,
            field_blacklist=self.field_blacklist,
            model_field_mapping=self.model_field_mapping,
            model_field_whitelist=self.model_field_whitelist,
            model_field_blacklist=self.model_field_blacklist,
        )

    def _build_procedure_policy(self) -> ProcedureAccessPolicy:
        """Builds the compiled procedure policy once.

        Returns:
            The compiled procedure access policy for this sort configuration.
        """
        if not self.procedure_whitelist and not self.procedure_blacklist:
            return DEFAULT_PROCEDURE_ACCESS_POLICY
        return _build_procedure_policy(
            self.procedure_whitelist,
            self.procedure_blacklist,
        )


def _normalize_nested_mapping(
    mapping: Mapping[type[Any], Mapping[str, _NestedValueT]],
) -> Mapping[type[Any], Mapping[str, _NestedValueT]]:
    """Normalizes nested mapping structures into immutable views.

    Returns:
        An immutable nested mapping copy.
    """
    return MappingProxyType(
        {
            model: MappingProxyType(dict(model_mapping))
            for model, model_mapping in mapping.items()
        },
    )


def _normalize_nested_sets(
    mapping: Mapping[type[Any], frozenset[str]],
) -> Mapping[type[Any], frozenset[str]]:
    """Normalizes nested set-like mappings into immutable views.

    Returns:
        An immutable nested set mapping copy.
    """
    return MappingProxyType(
        {model: frozenset(values) for model, values in mapping.items()},
    )
