"""Shared policy contracts and enforcement helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Mapping


class ProcedurePolicyProtocol(Protocol):
    """Structural contract for procedure access policies."""

    def is_whitelisted(self, function_name: str) -> bool:
        """Returns whether the function is allowed by the whitelist."""

    def is_blacklisted(self, function_name: str) -> bool:
        """Returns whether the function is blocked by the blacklist."""


class MappedFieldBindingOptions(Protocol):
    """Shared options contract for selector-binding stages."""

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


def enforce_field_access_policy(
    field_path: str,
    *,
    field_whitelist: frozenset[str] | set[str],
    field_blacklist: frozenset[str] | set[str],
    not_whitelisted_error_factory: callable,
    blacklisted_error_factory: callable,
) -> None:
    """Enforces whitelist/blacklist field access rules."""
    if field_path in field_blacklist:
        raise blacklisted_error_factory(
            f"Field {field_path!r} is blocked",
        )
    if field_whitelist and field_path not in field_whitelist:
        raise not_whitelisted_error_factory(
            f"Field {field_path!r} is not allowed",
        )


def enforce_function_access_policy(
    function_name: str,
    *,
    procedure_policy: ProcedurePolicyProtocol,
    not_whitelisted_error_factory: callable,
    blacklisted_error_factory: callable,
) -> None:
    """Enforces whitelist/blacklist procedure access rules."""
    if procedure_policy.is_blacklisted(function_name):
        raise blacklisted_error_factory(
            f"Function {function_name!r} is blacklisted",
        )
    if not procedure_policy.is_whitelisted(function_name):
        raise not_whitelisted_error_factory(
            f"Function {function_name!r} is not whitelisted",
        )
