"""Unit tests for SQLAlchemy JSON path expression building."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from sqlalchemy import column

from pyrsql.core.json.options import JSONOptions
from pyrsql.core.json.path import JSONPath
from pyrsql.core.json.query import JSONPathComparison

if TYPE_CHECKING:
    from pyrsql.orms.sqlalchemy.json_path import (
        SQLAlchemyJSONPathExpressionBuilder,
    )

pytestmark = [pytest.mark.sqlalchemy]


def _compile_sql(expression: Any, dialect: Any) -> Any:
    """Compiles one SQLAlchemy expression with the PostgreSQL dialect."""
    return expression.compile(dialect=dialect)


@pytest.mark.parametrize(
    ("options", "expected_function_name"),
    [
        pytest.param(None, "jsonb_path_exists", id="default-function"),
        pytest.param(
            JSONOptions(path_exists_function="custom_json_path_exists"),
            "custom_json_path_exists",
            id="custom-function",
        ),
    ],
)
def test_builder_casts_jsonpath_predicates_to_jsonpath(
    json_path_builder: SQLAlchemyJSONPathExpressionBuilder,
    postgresql_dialect: Any,
    options: JSONOptions | None,
    expected_function_name: str,
) -> None:
    """JSON path predicates use JSONPATH-typed binds for PostgreSQL."""
    predicate = json_path_builder.build_filter_expression(
        column("payload"),
        JSONPathComparison.from_raw_arguments(
            path=JSONPath(segments=("user", "id")),
            operator_name="equal",
            raw_arguments=(("1", False),),
        ),
        options=options,
    )
    compiled = _compile_sql(predicate, postgresql_dialect)

    assert expected_function_name in str(compiled)
    assert "CAST(%(param_1)s AS JSONPATH)" in str(compiled)


def test_builder_quotes_special_jsonpath_segments(
    json_path_builder: SQLAlchemyJSONPathExpressionBuilder,
    postgresql_dialect: Any,
) -> None:
    """PostgreSQL jsonpath output quotes non-identifier key segments."""
    predicate = json_path_builder.build_filter_expression(
        column("payload"),
        JSONPathComparison.from_raw_arguments(
            path=JSONPath(segments=("user name", "profile-id")),
            operator_name="equal",
            raw_arguments=(("demo", False),),
        ),
    )
    compiled = _compile_sql(predicate, postgresql_dialect)

    assert compiled.params["param_1"] == (
        '$."user name"."profile-id" ? (@ == "demo")'
    )


def test_builder_uses_jsonpath_vars_for_structured_values(
    json_path_builder: SQLAlchemyJSONPathExpressionBuilder,
    postgresql_dialect: Any,
) -> None:
    """Structured JSON values are passed through PostgreSQL vars payload."""
    predicate = json_path_builder.build_filter_expression(
        column("payload"),
        JSONPathComparison.from_raw_arguments(
            path=JSONPath(segments=("tags",)),
            operator_name="equal",
            raw_arguments=(("[1,2]", True),),
        ),
    )
    compiled = _compile_sql(predicate, postgresql_dialect)

    assert "CAST(%(param_2)s::JSONB AS JSONB)" in str(compiled)
    assert compiled.params["param_1"] == "$.tags ? (@ == $value_0)"
    assert compiled.params["param_2"] == {"value_0": [1, 2]}
