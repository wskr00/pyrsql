"""Security tests for SQLAlchemy-backed injection resistance."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.dialects import postgresql

import pyrsql
from pyrsql.core.json.options import JSONOptions
from pyrsql.core.options import QueryOptions
from pyrsql.orms.sqlalchemy import SQLAlchemyORM, SQLAlchemyORMError
from tests.integration.sqlalchemy.conftest import JsonEvent, User

pytestmark = [
    pytest.mark.security,
    pytest.mark.integration,
    pytest.mark.sqlalchemy,
]


def test_scalar_filter_payload_is_bound_as_parameter() -> None:
    """Treats SQL injection text as a scalar value, not SQL structure."""
    orm = SQLAlchemyORM()
    payload = "demo' OR 1=1 --"
    query = pyrsql.parse(
        "name=='demo\\' OR 1=1 --'",
        options=QueryOptions(strict_equality=True),
    )

    statement = orm.compile_query(query).apply(select(User), User)
    compiled = statement.compile()

    assert payload not in str(compiled)
    assert compiled.params["name_1"] == payload


def test_like_filter_payload_is_bound_as_parameter() -> None:
    """Treats LIKE payload text as a bound parameter, not inline SQL."""
    orm = SQLAlchemyORM()
    payload = "dem' OR 1=1 --"
    query = pyrsql.parse("name=like='dem\\' OR 1=1 --'")

    statement = orm.compile_query(query).apply(select(User), User)
    compiled = statement.compile()

    assert payload not in str(compiled)
    assert compiled.params["name_1"] == f"%{payload}%"


def test_jsonpath_string_payload_stays_out_of_sql_structure() -> None:
    """Keeps JSON path injection text inside a JSONPATH bind parameter."""
    orm = SQLAlchemyORM()
    payload = '" ) || true || (\\"'
    query = pyrsql.parse("""payload.name=='\\" ) || true || (\\\\"'""")

    statement = orm.compile_query(query).apply(select(JsonEvent), JsonEvent)
    compiled = statement.compile(dialect=postgresql.dialect())

    assert payload not in str(compiled)
    assert "CAST(%(param_1)s AS JSONPATH)" in str(compiled)
    assert '\\" ) || true || (\\\\\\""' in compiled.params["param_1"]


def test_sort_payload_is_rejected_by_model_resolution() -> None:
    """Rejects a malicious second sort clause as an unmapped attribute."""
    orm = SQLAlchemyORM()
    sort = pyrsql.Sort.parse("name,asc;DROP TABLE users")

    with pytest.raises(SQLAlchemyORMError, match="DROP TABLE users"):
        orm.compile_sort(sort).apply(select(User), User)


def test_json_options_reject_sql_function_name_injection() -> None:
    """Rejects unsafe SQL function names in JSON configuration."""
    with pytest.raises(ValueError, match="valid SQL identifier"):
        JSONOptions(path_exists_function="jsonb_path_exists;DROP_TABLE")
