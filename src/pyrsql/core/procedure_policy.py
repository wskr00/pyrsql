"""Shared procedure access-policy helpers."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import msgspec

if TYPE_CHECKING:
    from re import Pattern


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
            whitelist_patterns=tuple(
                re.compile(pattern) for pattern in whitelist
            ),
            blacklist_patterns=tuple(
                re.compile(pattern) for pattern in blacklist
            ),
        )

    def is_whitelisted(self, procedure_name: str) -> bool:
        """Whether the procedure matches the whitelist.

        Returns:
            ``True`` when the procedure matches at least one whitelist pattern.
        """
        return self._matches_any(procedure_name, self.whitelist_patterns)

    def is_blacklisted(self, procedure_name: str) -> bool:
        """Whether the procedure matches the blacklist.

        Returns:
            ``True`` when the procedure matches at least one blacklist pattern.
        """
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
        return any(pattern.fullmatch(procedure_name) for pattern in patterns)


DEFAULT_PROCEDURE_ACCESS_POLICY = ProcedureAccessPolicy(
    whitelist_patterns=(),
    blacklist_patterns=(),
)
