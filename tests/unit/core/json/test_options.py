"""Unit tests for orm-neutral JSON options."""

import pytest

from pyrsql.core.json.options import DEFAULT_JSON_OPTIONS, JSONOptions
from pyrsql.core.options import QueryOptions, SortOptions


def test_query_options_expose_default_json_options() -> None:
    """Query options carry JSON options by default."""
    options = QueryOptions()
    assert options.json_options is DEFAULT_JSON_OPTIONS


def test_sort_options_expose_default_json_options() -> None:
    """Sort options carry JSON options by default."""
    options = SortOptions()
    assert options.json_options is DEFAULT_JSON_OPTIONS


def test_query_options_accept_json_options_override() -> None:
    """Query options accept explicit JSON option overrides."""
    options = QueryOptions(json_options=JSONOptions(use_datetime=True))
    assert options.json_options.use_datetime is True


def test_json_options_accept_function_name_overrides() -> None:
    """JSON options expose configurable PostgreSQL function names."""
    options = JSONOptions(
        path_exists_function="custom_path_exists",
        path_exists_tz_function="custom_path_exists_tz",
    )
    assert options.path_exists_function == "custom_path_exists"
    assert options.path_exists_tz_function == "custom_path_exists_tz"


def test_json_options_reject_invalid_function_names() -> None:
    """JSON options reject malformed SQL function identifiers."""
    with pytest.raises(ValueError, match="valid SQL identifier"):
        JSONOptions(path_exists_function="bad-name")

    with pytest.raises(ValueError, match="outer whitespace"):
        JSONOptions(path_exists_tz_function=" jsonb_path_exists_tz ")
