"""Errors raised while parsing or binding sort expressions."""

from dataclasses import dataclass
from typing import ClassVar

from pyrsql.sorting.diagnostics import SortDiagnostic


@dataclass(frozen=True, slots=True)
class SortError(ValueError):
    """Base exception for sorting failures."""

    message: str
    code: ClassVar[str] = "sort_error"

    @property
    def diagnostic(self) -> SortDiagnostic:
        """Returns the structured diagnostic for this error.

        Returns:
            The structured sorting diagnostic.
        """
        return SortDiagnostic(code=self.code, message=self.message)

    def __str__(self) -> str:
        """Formats the sort error consistently.

        Returns:
            The formatted sort error string.
        """
        return str(self.diagnostic)


@dataclass(frozen=True, slots=True)
class SortParseError(SortError):
    """Raised when a sort expression is malformed."""

    code: ClassVar[str] = "sort_parse_error"


@dataclass(frozen=True, slots=True)
class SortFieldNotWhitelistedError(SortError):
    """Raised when a sort selector is not allowed by the whitelist."""

    code: ClassVar[str] = "sort_field_not_whitelisted"


@dataclass(frozen=True, slots=True)
class SortFieldBlacklistedError(SortError):
    """Raised when a sort selector is blocked by the blacklist."""

    code: ClassVar[str] = "sort_field_blacklisted"


@dataclass(frozen=True, slots=True)
class SortFunctionNotWhitelistedError(SortError):
    """Raised when a sort function is not allowed by the whitelist."""

    code: ClassVar[str] = "sort_function_not_whitelisted"


@dataclass(frozen=True, slots=True)
class SortFunctionBlacklistedError(SortError):
    """Raised when a sort function is blocked by the blacklist."""

    code: ClassVar[str] = "sort_function_blacklisted"
