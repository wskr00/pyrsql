"""Shared query options."""

from dataclasses import dataclass
from dataclasses import field
from types import MappingProxyType
from typing import Mapping

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
        if (
            self.like_escape_character is not None
            and len(self.like_escape_character) != 1
        ):
            raise ValueError(
                "like_escape_character must be a single character when set."
            )


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
