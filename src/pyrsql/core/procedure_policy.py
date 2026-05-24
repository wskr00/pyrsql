"""Shared procedure access-policy helpers."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

import msgspec

if TYPE_CHECKING:
    from re import Pattern

_COMPILED_PATTERN_TYPE: Final = type(re.compile(r""))


def _compile_pattern(pattern: str, *, context: str) -> Pattern[str]:
    """Compiles one raw regex pattern with contextual errors.

    Returns:
        One compiled regular expression.

    Raises:
        ValueError: If the regular expression is invalid.
    """
    try:
        return re.compile(pattern)
    except re.error as error:
        raise ValueError(
            f"Invalid {context} regex pattern {pattern!r}.",
        ) from error


def _compile_patterns(
    patterns: tuple[str, ...],
    *,
    context: str,
) -> tuple[Pattern[str], ...]:
    """Compiles raw regex patterns with contextual errors.

    Returns:
        Compiled regular expressions in declaration order.
    """
    return tuple(
        _compile_pattern(pattern, context=context) for pattern in patterns
    )


def _normalize_compiled_patterns(
    patterns: tuple[Pattern[str], ...],
    *,
    context: str,
) -> tuple[Pattern[str], ...]:
    """Normalizes and validates compiled regex patterns.

    Returns:
        The validated compiled regular expressions.

    Raises:
        TypeError: If any pattern is not a compiled regular expression.
    """
    normalized = tuple(patterns)
    for pattern in normalized:
        if not isinstance(pattern, _COMPILED_PATTERN_TYPE):
            raise TypeError(
                f"{context} must contain compiled regular expressions.",
            )
    return normalized


class ProcedureAccessPolicy(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
):
    """Regex-based access policy for selector procedures.

    The policy stores compiled whitelist and blacklist patterns used to check
    whether a procedure name is allowed.

    Attributes:
        whitelist_patterns: Compiled whitelist regular expressions.
        blacklist_patterns: Compiled blacklist regular expressions.
    """

    whitelist_patterns: tuple[Pattern[str], ...]
    blacklist_patterns: tuple[Pattern[str], ...]

    def __post_init__(self) -> None:
        """Normalizes and validates compiled regex patterns."""
        msgspec.structs.force_setattr(
            self,
            "whitelist_patterns",
            _normalize_compiled_patterns(
                self.whitelist_patterns,
                context="whitelist_patterns",
            ),
        )
        msgspec.structs.force_setattr(
            self,
            "blacklist_patterns",
            _normalize_compiled_patterns(
                self.blacklist_patterns,
                context="blacklist_patterns",
            ),
        )

    @classmethod
    def from_patterns(
        cls,
        whitelist: tuple[str, ...],
        blacklist: tuple[str, ...],
    ) -> ProcedureAccessPolicy:
        """Builds a policy from raw regex pattern strings.

        Args:
            whitelist: Raw regular expressions that allow procedures.
            blacklist: Raw regular expressions that deny procedures.

        Returns:
            A compiled procedure access policy.
        """
        return cls(
            whitelist_patterns=_compile_patterns(
                whitelist,
                context="whitelist",
            ),
            blacklist_patterns=_compile_patterns(
                blacklist,
                context="blacklist",
            ),
        )

    def is_whitelisted(self, procedure_name: str) -> bool:
        """Whether the procedure matches the whitelist.

        Returns:
            ``True`` when the procedure matches at least one whitelist pattern.
        """
        if not self.whitelist_patterns:
            return False
        return self._matches_any(procedure_name, self.whitelist_patterns)

    def is_blacklisted(self, procedure_name: str) -> bool:
        """Whether the procedure matches the blacklist.

        Returns:
            ``True`` when the procedure matches at least one blacklist pattern.
        """
        if not self.blacklist_patterns:
            return False
        return self._matches_any(procedure_name, self.blacklist_patterns)

    @staticmethod
    def _matches_any(
        procedure_name: str,
        patterns: tuple[Pattern[str], ...],
    ) -> bool:
        """Whether a value fully matches at least one pattern.

        Returns:
            ``True`` when the value fully matches at least one pattern.
        """
        for pattern in patterns:
            if pattern.fullmatch(procedure_name) is not None:
                return True
        return False


DEFAULT_PROCEDURE_ACCESS_POLICY = ProcedureAccessPolicy(
    whitelist_patterns=(),
    blacklist_patterns=(),
)
