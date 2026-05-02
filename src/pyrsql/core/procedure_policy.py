"""Shared procedure access-policy helpers."""

import re
from dataclasses import dataclass
from re import Pattern


@dataclass(frozen=True, slots=True)
class ProcedureAccessPolicy:
    """Immutable regex-based access policy for selector procedures."""

    whitelist_patterns: tuple[Pattern[str], ...]
    blacklist_patterns: tuple[Pattern[str], ...]

    @classmethod
    def from_patterns(
        cls,
        whitelist: tuple[str, ...],
        blacklist: tuple[str, ...],
    ) -> "ProcedureAccessPolicy":
        """Builds a policy from raw regex pattern strings."""
        return cls(
            whitelist_patterns=tuple(
                re.compile(pattern) for pattern in whitelist
            ),
            blacklist_patterns=tuple(
                re.compile(pattern) for pattern in blacklist
            ),
        )

    def is_whitelisted(self, procedure_name: str) -> bool:
        """Returns whether the procedure matches the whitelist."""
        return self._matches_any(procedure_name, self.whitelist_patterns)

    def is_blacklisted(self, procedure_name: str) -> bool:
        """Returns whether the procedure matches the blacklist."""
        return self._matches_any(procedure_name, self.blacklist_patterns)

    def _matches_any(
        self,
        procedure_name: str,
        patterns: tuple[Pattern[str], ...],
    ) -> bool:
        """Returns whether a value fully matches at least one pattern."""
        return any(pattern.fullmatch(procedure_name) for pattern in patterns)
