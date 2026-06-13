"""Security tests for JSON path regex and wildcard handling."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.dialects import postgresql

import pyrsql
from pyrsql.orms.sqlalchemy import SQLAlchemyORM
from tests.integration.sqlalchemy.conftest import JsonEvent

pytestmark = [
    pytest.mark.security,
    pytest.mark.integration,
    pytest.mark.sqlalchemy,
]


def test_json_like_escapes_regex_metacharacters_but_keeps_wildcards() -> None:
    """Treats only ``*`` as wildcard while escaping other regex syntax."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse(r"""payload.name=like='a.*(b)[c]{2}|^$'""")

    statement = orm.compile_query(query).apply(select(JsonEvent), JsonEvent)
    compiled = statement.compile(dialect=postgresql.dialect())
    rendered_path = compiled.params["param_1"]

    assert "CAST(%(param_1)s AS JSONPATH)" in str(compiled)
    assert r"a\\..*" in rendered_path
    assert r"\\(b\\)\\[c\\]\\{2\\}\\|\\^\\$" in rendered_path


def test_json_ilike_keeps_ignore_case_flag_inside_bound_jsonpath() -> None:
    """Keeps case-insensitive regex flags inside the JSONPATH bind."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse("""payload.name=ilike='Demo'""")

    statement = orm.compile_query(query).apply(select(JsonEvent), JsonEvent)
    compiled = statement.compile(dialect=postgresql.dialect())

    assert 'flag "i"' not in str(compiled)
    assert 'flag "i"' in compiled.params["param_1"]


def test_json_notlike_payload_stays_escaped_inside_jsonpath_bind() -> None:
    """Treats malicious NOT LIKE payload text as escaped regex content."""
    orm = SQLAlchemyORM()
    payload = 'x" ) || true || (\\\\"'
    query = pyrsql.parse(r"""payload.name=notlike='x\" ) || true || (\\\"'""")

    statement = orm.compile_query(query).apply(select(JsonEvent), JsonEvent)
    compiled = statement.compile(dialect=postgresql.dialect())

    assert payload not in str(compiled)
    assert "@ like_regex" in compiled.params["param_1"]
    assert "|| true ||" not in compiled.params["param_1"]
    assert '\\"' in compiled.params["param_1"]


def test_json_equality_with_wildcard_uses_bound_jsonpath_regex() -> None:
    """Treats wildcard equality on JSON strings as regex over a bind value."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse("""payload.name=='dem*o'""")

    statement = orm.compile_query(query).apply(select(JsonEvent), JsonEvent)
    compiled = statement.compile(dialect=postgresql.dialect())

    assert "CAST(%(param_1)s AS JSONPATH)" in str(compiled)
    assert 'like_regex "dem.*o"' in compiled.params["param_1"]
