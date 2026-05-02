"""Unit tests for backend-neutral JSON options."""

from pyrsql.core.json.options import JSONOptions
from pyrsql.core.options import QueryOptions
from pyrsql.core.options import SortOptions


def test_query_options_expose_default_json_options() -> None:
    """Query options carry JSON options by default."""
    options = QueryOptions()
    assert options.json_options == JSONOptions()


def test_sort_options_expose_default_json_options() -> None:
    """Sort options carry JSON options by default."""
    options = SortOptions()
    assert options.json_options == JSONOptions()


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
