"""Shared query options."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final, Protocol, TypeVar

import msgspec

from pyrsql.core.conversion import (
    DEFAULT_FIELD_VALUE_CONVERTER_SET,
    DEFAULT_VALUE_CONVERTER_REGISTRY,
    FieldValueConverterSet,
)
from pyrsql.core.field_policy import DEFAULT_FIELD_POLICY_SET, FieldPolicySet
from pyrsql.core.json.options import DEFAULT_JSON_OPTIONS
from pyrsql.core.procedure_policy import (
    DEFAULT_PROCEDURE_ACCESS_POLICY,
    ProcedureAccessPolicy,
)
from pyrsql.parsing.limits import DEFAULT_PARSE_LIMITS
from pyrsql.parsing.operators import DEFAULT_OPERATOR_REGISTRY, OperatorRegistry
from pyrsql.sorting.limits import DEFAULT_SORT_LIMITS

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pyrsql.core.conversion import (
        ValueConverter,
        ValueConverterRegistry,
    )
    from pyrsql.core.custom import CustomPredicateDefinition
    from pyrsql.core.joins import JoinHint
    from pyrsql.core.json.options import JSONOptions
    from pyrsql.parsing.limits import ParseLimits
    from pyrsql.sorting.limits import SortLimits

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
    msgspec.structs.force_setattr(
        options,
        "field_mapping",
        _normalize_mapping(options.field_mapping),
    )
    msgspec.structs.force_setattr(
        options,
        "model_field_mapping",
        _normalize_nested_mapping(options.model_field_mapping),
    )
    msgspec.structs.force_setattr(
        options,
        "join_hints",
        _normalize_mapping(options.join_hints),
    )
    msgspec.structs.force_setattr(
        options,
        "field_whitelist",
        _normalize_frozenset(options.field_whitelist),
    )
    msgspec.structs.force_setattr(
        options,
        "field_blacklist",
        _normalize_frozenset(options.field_blacklist),
    )
    msgspec.structs.force_setattr(
        options,
        "model_field_whitelist",
        _normalize_nested_sets(options.model_field_whitelist),
    )
    msgspec.structs.force_setattr(
        options,
        "model_field_blacklist",
        _normalize_nested_sets(options.model_field_blacklist),
    )
    msgspec.structs.force_setattr(
        options,
        "procedure_whitelist",
        _normalize_tuple(options.procedure_whitelist),
    )
    msgspec.structs.force_setattr(
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
        field_whitelist=field_whitelist,
        field_blacklist=field_blacklist,
        model_field_mapping=model_field_mapping,
        model_field_whitelist=model_field_whitelist,
        model_field_blacklist=model_field_blacklist,
    )


def _has_field_policy_configuration(
    *,
    field_whitelist: frozenset[str],
    field_blacklist: frozenset[str],
    model_field_mapping: Mapping[type[Any], Mapping[str, str]],
    model_field_whitelist: Mapping[type[Any], frozenset[str]],
    model_field_blacklist: Mapping[type[Any], frozenset[str]],
) -> bool:
    """Whether any runtime field-policy settings are configured.

    Returns:
        ``True`` when at least one runtime field-policy option is configured.
    """
    return any(
        (
            field_whitelist,
            field_blacklist,
            model_field_mapping,
            model_field_whitelist,
            model_field_blacklist,
        ),
    )


def _resolve_field_policy(
    *,
    field_whitelist: frozenset[str],
    field_blacklist: frozenset[str],
    model_field_mapping: Mapping[type[Any], Mapping[str, str]],
    model_field_whitelist: Mapping[type[Any], frozenset[str]],
    model_field_blacklist: Mapping[type[Any], frozenset[str]],
) -> FieldPolicySet:
    """Builds one field policy, reusing the shared default when empty.

    Returns:
        A normalized field policy instance.
    """
    if not _has_field_policy_configuration(
        field_whitelist=field_whitelist,
        field_blacklist=field_blacklist,
        model_field_mapping=model_field_mapping,
        model_field_whitelist=model_field_whitelist,
        model_field_blacklist=model_field_blacklist,
    ):
        return DEFAULT_FIELD_POLICY_SET
    return _build_field_policy(
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


def _resolve_procedure_policy(
    whitelist: tuple[str, ...],
    blacklist: tuple[str, ...],
) -> ProcedureAccessPolicy:
    """Builds one procedure policy, reusing the shared default when empty.

    Returns:
        A compiled procedure access policy instance.
    """
    if not whitelist and not blacklist:
        return DEFAULT_PROCEDURE_ACCESS_POLICY
    return _build_procedure_policy(whitelist, blacklist)


class QueryOptions(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """ORM-neutral configuration for parsing and compiling queries.

    The options bundle parser limits, operator registries, field policies,
    custom predicates, value converters, and JSON behavior in one immutable
    object.
    """

    strict_equality: bool = False
    distinct: bool = False
    like_escape_character: str | None = None
    field_mapping: Mapping[str, str] = {}
    model_field_mapping: Mapping[type[Any], Mapping[str, str]] = {}
    join_hints: Mapping[str, JoinHint] = {}
    field_whitelist: frozenset[str] = frozenset()
    field_blacklist: frozenset[str] = frozenset()
    model_field_whitelist: Mapping[type[Any], frozenset[str]] = {}
    model_field_blacklist: Mapping[type[Any], frozenset[str]] = {}
    procedure_whitelist: tuple[str, ...] = ()
    procedure_blacklist: tuple[str, ...] = ()
    parse_limits: ParseLimits = DEFAULT_PARSE_LIMITS
    operator_registry: OperatorRegistry = DEFAULT_OPERATOR_REGISTRY
    custom_predicates: Mapping[str, CustomPredicateDefinition] = {}
    value_converter_registry: ValueConverterRegistry = (
        DEFAULT_VALUE_CONVERTER_REGISTRY
    )
    field_value_converters: Mapping[str, ValueConverter] = {}
    model_field_value_converters: Mapping[
        type[Any],
        Mapping[str, ValueConverter],
    ] = {}
    json_options: JSONOptions = msgspec.field(
        default_factory=lambda: DEFAULT_JSON_OPTIONS,
    )
    _field_policy: FieldPolicySet = DEFAULT_FIELD_POLICY_SET
    _field_converter_set: FieldValueConverterSet = (
        DEFAULT_FIELD_VALUE_CONVERTER_SET
    )
    _procedure_policy: ProcedureAccessPolicy = DEFAULT_PROCEDURE_ACCESS_POLICY

    def __post_init__(self) -> None:
        """Normalizes option containers into immutable representations."""
        _normalize_shared_policy_options(self)
        msgspec.structs.force_setattr(
            self,
            "field_value_converters",
            _normalize_mapping(self.field_value_converters),
        )
        msgspec.structs.force_setattr(
            self,
            "model_field_value_converters",
            _normalize_nested_mapping(self.model_field_value_converters),
        )
        msgspec.structs.force_setattr(
            self,
            "custom_predicates",
            _normalize_mapping(self.custom_predicates),
        )
        msgspec.structs.force_setattr(
            self,
            "operator_registry",
            self._build_operator_registry(),
        )
        _validate_like_escape_character(self.like_escape_character)
        msgspec.structs.force_setattr(
            self,
            "_field_policy",
            _resolve_field_policy(
                field_whitelist=self.field_whitelist,
                field_blacklist=self.field_blacklist,
                model_field_mapping=self.model_field_mapping,
                model_field_whitelist=self.model_field_whitelist,
                model_field_blacklist=self.model_field_blacklist,
            ),
        )
        msgspec.structs.force_setattr(
            self,
            "_field_converter_set",
            self._build_field_converter_set(),
        )
        msgspec.structs.force_setattr(
            self,
            "_procedure_policy",
            _resolve_procedure_policy(
                self.procedure_whitelist,
                self.procedure_blacklist,
            ),
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

    def with_field_whitelist(
        self,
        field_whitelist: frozenset[str],
    ) -> QueryOptions:
        """Returns one copy with only the global field whitelist replaced.

        Returns:
            A query options copy with the provided field whitelist.
        """
        return QueryOptions(
            strict_equality=self.strict_equality,
            distinct=self.distinct,
            like_escape_character=self.like_escape_character,
            field_mapping=self.field_mapping,
            model_field_mapping=self.model_field_mapping,
            join_hints=self.join_hints,
            field_whitelist=field_whitelist,
            field_blacklist=self.field_blacklist,
            model_field_whitelist=self.model_field_whitelist,
            model_field_blacklist=self.model_field_blacklist,
            procedure_whitelist=self.procedure_whitelist,
            procedure_blacklist=self.procedure_blacklist,
            parse_limits=self.parse_limits,
            operator_registry=self.operator_registry,
            custom_predicates=self.custom_predicates,
            value_converter_registry=self.value_converter_registry,
            field_value_converters=self.field_value_converters,
            model_field_value_converters=self.model_field_value_converters,
            json_options=self.json_options,
        )


class SortOptions(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """ORM-neutral sort options."""

    field_mapping: Mapping[str, str] = {}
    model_field_mapping: Mapping[type[Any], Mapping[str, str]] = {}
    join_hints: Mapping[str, JoinHint] = {}
    field_whitelist: frozenset[str] = frozenset()
    field_blacklist: frozenset[str] = frozenset()
    model_field_whitelist: Mapping[type[Any], frozenset[str]] = {}
    model_field_blacklist: Mapping[type[Any], frozenset[str]] = {}
    procedure_whitelist: tuple[str, ...] = ()
    procedure_blacklist: tuple[str, ...] = ()
    sort_limits: SortLimits = DEFAULT_SORT_LIMITS
    json_options: JSONOptions = msgspec.field(
        default_factory=lambda: DEFAULT_JSON_OPTIONS,
    )
    _field_policy: FieldPolicySet = DEFAULT_FIELD_POLICY_SET
    _procedure_policy: ProcedureAccessPolicy = DEFAULT_PROCEDURE_ACCESS_POLICY

    def __post_init__(self) -> None:
        """Normalizes option containers into immutable representations."""
        _normalize_shared_policy_options(self)
        msgspec.structs.force_setattr(
            self,
            "_field_policy",
            _resolve_field_policy(
                field_whitelist=self.field_whitelist,
                field_blacklist=self.field_blacklist,
                model_field_mapping=self.model_field_mapping,
                model_field_whitelist=self.model_field_whitelist,
                model_field_blacklist=self.model_field_blacklist,
            ),
        )
        msgspec.structs.force_setattr(
            self,
            "_procedure_policy",
            _resolve_procedure_policy(
                self.procedure_whitelist,
                self.procedure_blacklist,
            ),
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

    def with_field_whitelist(
        self,
        field_whitelist: frozenset[str],
    ) -> SortOptions:
        """Returns one copy with only the global field whitelist replaced.

        Returns:
            A sort options copy with the provided field whitelist.
        """
        return SortOptions(
            field_mapping=self.field_mapping,
            model_field_mapping=self.model_field_mapping,
            join_hints=self.join_hints,
            field_whitelist=field_whitelist,
            field_blacklist=self.field_blacklist,
            model_field_whitelist=self.model_field_whitelist,
            model_field_blacklist=self.model_field_blacklist,
            procedure_whitelist=self.procedure_whitelist,
            procedure_blacklist=self.procedure_blacklist,
            sort_limits=self.sort_limits,
            json_options=self.json_options,
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
