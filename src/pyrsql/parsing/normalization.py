"""Shared runtime normalization helpers for parsing components."""

from __future__ import annotations

from pyrsql.parsing.limits import DEFAULT_PARSE_LIMITS, ParseLimits
from pyrsql.parsing.operators import (
    OperatorRegistry,
)


def normalize_parse_limits(
    limits: ParseLimits | None,
    *,
    owner_type: type[object],
) -> ParseLimits:
    """Normalizes optional parser limits.

    Returns:
        The provided limits, or the shared defaults.

    Raises:
        TypeError: If ``limits`` is not a ``ParseLimits`` instance.
    """
    if limits is None:
        return DEFAULT_PARSE_LIMITS
    if not isinstance(limits, ParseLimits):
        raise TypeError(
            f"{owner_type.__name__} limits must be a ParseLimits instance.",
        )
    return limits


def normalize_operator_registry(
    operator_registry: OperatorRegistry,
    *,
    owner_type: type[object],
) -> OperatorRegistry:
    """Normalizes the operator registry dependency.

    Returns:
        The validated operator registry instance.

    Raises:
        TypeError: If the registry is not an ``OperatorRegistry``.
    """
    if not isinstance(operator_registry, OperatorRegistry):
        raise TypeError(
            f"{owner_type.__name__} operator_registry must be an "
            "OperatorRegistry instance.",
        )
    return operator_registry
