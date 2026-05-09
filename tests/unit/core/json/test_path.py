"""Unit tests for orm-neutral JSON path primitives."""

import pytest

from pyrsql.core.json.path import JSONPath


def test_json_path_rejects_empty_segments() -> None:
    """JSON paths reject empty path segments."""
    with pytest.raises(ValueError, match="(?i)empty"):
        JSONPath(segments=("user", ""))


def test_json_path_reports_root_and_dot_path() -> None:
    """JSON paths expose root and dotted representations."""
    root_path = JSONPath()
    nested_path = JSONPath(segments=("user", "id"))
    assert root_path.is_root is True
    assert nested_path.is_root is False
    assert nested_path.to_dot_path() == "user.id"
    assert root_path.to_postgresql_jsonpath() == "$"
    assert nested_path.to_postgresql_jsonpath() == "$.user.id"


def test_json_path_quotes_postgresql_special_segments() -> None:
    """JSON paths quote PostgreSQL segments that are not simple identifiers."""
    path = JSONPath(segments=("user name", "x-y", 'quote"key'))
    assert (
        path.to_postgresql_jsonpath()
        == '$."user name"."x-y"."quote\\"key"'
    )


def test_json_path_rejects_segments_with_outer_whitespace() -> None:
    """JSON paths reject whitespace-padded segments."""
    with pytest.raises(ValueError, match="outer whitespace"):
        JSONPath(segments=(" user ",))
