"""Unit tests for SQLAlchemy JSON path expression building."""

# pylint: disable=wrong-import-position,unsubscriptable-object

from typing import Any

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.sqlalchemy]

sqlalchemy = pytest.importorskip("sqlalchemy")

from sqlalchemy import column
from sqlalchemy.dialects import postgresql

from pyrsql.core.json.options import JSONOptions
from pyrsql.core.json.path import JSONPath
from pyrsql.core.json.query import JSONPathComparison
from pyrsql.orms.sqlalchemy.json_path import (
    SQLAlchemyJSONPathExpressionBuilder,
)


def test_builder_casts_default_jsonpath_predicates_to_jsonpath() -> None:
    """Default JSON path predicates use a JSONPATH-typed bind."""
    builder = SQLAlchemyJSONPathExpressionBuilder()
    predicate = builder.build_filter_expression(
        column("payload"),
        JSONPathComparison.from_raw_arguments(
            path=JSONPath(segments=("user", "id")),
            operator_name="equal",
            raw_arguments=(("1", False),),
        ),
    )
    dialect: Any = postgresql.dialect()  # type: ignore[no-untyped-call]
    compiled = predicate.compile(dialect=dialect)
    assert "jsonb_path_exists" in str(compiled)
    assert "CAST(%(param_1)s AS JSONPATH)" in str(compiled)


def test_builder_quotes_special_jsonpath_segments() -> None:
    """PostgreSQL jsonpath output quotes non-identifier key segments."""
    builder = SQLAlchemyJSONPathExpressionBuilder()
    predicate = builder.build_filter_expression(
        column("payload"),
        JSONPathComparison.from_raw_arguments(
            path=JSONPath(segments=("user name", "profile-id")),
            operator_name="equal",
            raw_arguments=(("demo", False),),
        ),
    )
    dialect: Any = postgresql.dialect()  # type: ignore[no-untyped-call]
    compiled = predicate.compile(dialect=dialect)
    assert compiled.params["param_1"] == (
        '$."user name"."profile-id" ? (@ == "demo")'
    )


def test_builder_uses_jsonpath_vars_for_structured_values() -> None:
    """Structured JSON values are passed through PostgreSQL vars payload."""
    builder = SQLAlchemyJSONPathExpressionBuilder()
    predicate = builder.build_filter_expression(
        column("payload"),
        JSONPathComparison.from_raw_arguments(
            path=JSONPath(),
            operator_name="equal",
            raw_arguments=(('[1,2]', True),),
        ),
    )
    dialect: Any = postgresql.dialect()  # type: ignore[no-untyped-call]
    compiled = predicate.compile(dialect=dialect)
    assert "CAST(%(param_2)s::JSONB AS JSONB)" in str(compiled)
    assert compiled.params["param_1"] == "$ ? (@ == $value_0)"
    assert compiled.params["param_2"] == {"value_0": [1, 2]}


def test_builder_casts_custom_path_exists_function_arguments() -> None:
    """Custom JSON path function names still receive JSONPATH-typed binds."""
    builder = SQLAlchemyJSONPathExpressionBuilder()
    predicate = builder.build_filter_expression(
        column("payload"),
        JSONPathComparison.from_raw_arguments(
            path=JSONPath(segments=("user", "id")),
            operator_name="equal",
            raw_arguments=(("1", False),),
        ),
        options=JSONOptions(path_exists_function="custom_json_path_exists"),
    )
    dialect: Any = postgresql.dialect()  # type: ignore[no-untyped-call]
    compiled = predicate.compile(dialect=dialect)
    assert "custom_json_path_exists" in str(compiled)
    assert "CAST(%(param_1)s AS JSONPATH)" in str(compiled)
