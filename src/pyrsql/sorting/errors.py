"""Errors raised while parsing or analyzing sort expressions."""


class SortParseError(ValueError):
    """Raised when a sort expression is malformed."""


class SortFieldNotWhitelistedError(ValueError):
    """Raised when a sort selector is not allowed by the whitelist."""


class SortFieldBlacklistedError(ValueError):
    """Raised when a sort selector is blocked by the blacklist."""


class SortFunctionNotWhitelistedError(ValueError):
    """Raised when a sort function is not allowed by the whitelist."""


class SortFunctionBlacklistedError(ValueError):
    """Raised when a sort function is blocked by the blacklist."""
