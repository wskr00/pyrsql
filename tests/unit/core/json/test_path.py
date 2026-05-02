"""Unit tests for backend-neutral JSON path primitives."""

import pytest

from pyrsql.core.json.path import JSONPath


def test_json_path_rejects_empty_segments() -> None:
    """JSON paths reject empty path segments."""
    with pytest.raises(ValueError):
        JSONPath(("user", ""))


def test_json_path_reports_root_and_dot_path() -> None:
    """JSON paths expose root and dotted representations."""
    root_path = JSONPath()
    nested_path = JSONPath(("user", "id"))
    assert root_path.is_root is True
    assert nested_path.is_root is False
    assert nested_path.to_dot_path() == "user.id"
