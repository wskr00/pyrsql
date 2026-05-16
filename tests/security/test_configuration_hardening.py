"""Security tests for configuration-level hardening guarantees."""

from __future__ import annotations

import pytest

from pyrsql.core.json.options import JSONOptions
from pyrsql.core.options import QueryOptions, SortOptions

pytestmark = [pytest.mark.security]


def test_json_options_reject_path_exists_tz_function_injection() -> None:
    """Rejects unsafe timezone-aware JSON path function names."""
    with pytest.raises(ValueError, match="valid SQL identifier"):
        JSONOptions(path_exists_tz_function="jsonb_path_exists_tz;DROP")


def test_query_procedure_whitelist_requires_full_function_match() -> None:
    """Does not treat partial procedure-name matches as whitelisted."""
    options = QueryOptions(procedure_whitelist=("upper",))

    assert options.procedure_policy.is_whitelisted("upper_suffix") is False


def test_sort_procedure_whitelist_requires_full_function_match() -> None:
    """Applies full regex matching to sort procedure allowlists as well."""
    options = SortOptions(procedure_whitelist=("upper",))

    assert options.procedure_policy.is_whitelisted("upper_suffix") is False
