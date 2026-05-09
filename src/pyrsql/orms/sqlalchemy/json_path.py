"""JSON path expression building for the SQLAlchemy orm."""

import json
import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, cast

import msgspec
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.elements import ColumnElement

from pyrsql.core.json.options import DEFAULT_JSON_OPTIONS, JSONOptions
from pyrsql.core.json.path import JSONPath
from pyrsql.core.json.query import JSONPathComparison
from pyrsql.core.json.values import JSONScalarValue
from pyrsql.orms.sqlalchemy.errors import SQLAlchemyORMError
from pyrsql.parsing.operators import (
    BETWEEN,
    EQUAL,
    GREATER_THAN,
    GREATER_THAN_OR_EQUAL,
    IGNORE_CASE,
    IGNORE_CASE_LIKE,
    IGNORE_CASE_NOT_LIKE,
    IN,
    IS_NULL,
    LESS_THAN,
    LESS_THAN_OR_EQUAL,
    LIKE,
    NOT_BETWEEN,
    NOT_EQUAL,
    NOT_IN,
    NOT_LIKE,
    NOT_NULL,
)

_ISO_DATE_TIME_PATTERN_TZ = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
)
_ISO_TIME_PATTERN_TZ = re.compile(
    r"^\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
)
_ISO_DATE_TIME_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$"
)
_ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ISO_TIME_PATTERN = re.compile(r"^\d{2}:\d{2}:\d{2}(\.\d+)?$")


class SQLAlchemyJSONPathExpressionBuilder:
    """Builds PostgreSQL JSON path expressions for SQLAlchemy."""

    __slots__ = ()

    def build_filter_expression(
        self,
        column: ColumnElement[Any],
        comparison: JSONPathComparison,
        *,
        options: JSONOptions | None = None,
    ) -> ColumnElement[bool]:
        """Builds a PostgreSQL JSONB path-exists predicate."""
        function_call = self._build_filter_call(
            comparison,
            options=options or DEFAULT_JSON_OPTIONS,
        )
        jsonb_column = cast(
            ColumnElement[Any],
            sa.cast(column, postgresql.JSONB),
        )
        json_path_literal = self._jsonpath_literal(
            function_call.json_path_expression
        )
        vars_payload = self._jsonpath_vars_payload(function_call.vars_payload)
        if function_call.use_timezone_function:
            function_expression = getattr(
                sa.func,
                function_call.path_exists_tz_function,
            )(
                jsonb_column,
                json_path_literal,
                vars_payload,
            )
            return cast(ColumnElement[bool], function_expression)
        if options and options.path_exists_function != "jsonb_path_exists":
            function_expression = getattr(
                sa.func,
                options.path_exists_function,
            )(
                jsonb_column,
                json_path_literal,
                vars_payload,
            )
            return cast(ColumnElement[bool], function_expression)
        return cast(
            ColumnElement[bool],
            sa.func.jsonb_path_exists(  # pylint: disable=not-callable
                jsonb_column,
                json_path_literal,
                vars_payload,
            ),
        )

    def _jsonpath_literal(self, expression: str) -> ColumnElement[Any]:
        """Builds one JSONPATH-typed literal for PostgreSQL predicates."""
        return cast(
            ColumnElement[Any],
            sa.cast(sa.literal(expression), postgresql.JSONPATH),
        )

    def _jsonpath_vars_payload(
        self,
        vars_payload: Mapping[str, Any],
    ) -> ColumnElement[Any]:
        """Builds the JSONB vars payload passed to PostgreSQL jsonpath funcs."""
        return cast(
            ColumnElement[Any],
            sa.cast(
                sa.literal(dict(vars_payload), type_=postgresql.JSONB),
                postgresql.JSONB,
            ),
        )

    def build_sort_expression(
        self,
        column: ColumnElement[Any],
        json_path: JSONPath,
    ) -> ColumnElement[Any]:
        """Builds a PostgreSQL JSON path extraction expression for sort."""
        jsonb_column = cast(
            ColumnElement[Any],
            sa.cast(column, postgresql.JSONB),
        )
        if json_path.is_root:
            return jsonb_column
        return cast(
            ColumnElement[Any],
            jsonb_column[json_path.segments].as_string(),
        )

    def _build_filter_call(
        self,
        comparison: JSONPathComparison,
        *,
        options: JSONOptions,
    ) -> "_JSONPathFilterCall":
        """Builds the function call payload for one jsonpath predicate."""
        target_path = comparison.path.to_postgresql_jsonpath()
        use_datetime = options.use_datetime
        use_timezone_function = use_datetime and any(
            self._is_timezone_datetime_value(value)
            for value in comparison.values
        )
        vars_payload: dict[str, Any] = {}
        value_reference = "@"
        if use_datetime and any(
            self._is_datetime_value(value) for value in comparison.values
        ):
            value_reference = "@.datetime()"
        if comparison.operator_name == NOT_NULL.name:
            comparison_clause = "(@ != null)"
        elif comparison.operator_name == EQUAL.name:
            comparison_clause = self._equality_comparison(
                comparison.values[0],
                variable_name="value_0",
                vars_payload=vars_payload,
                use_datetime=use_datetime,
            )
        elif comparison.operator_name == NOT_EQUAL.name:
            equality_clause = self._equality_comparison(
                comparison.values[0],
                variable_name="value_0",
                vars_payload=vars_payload,
                use_datetime=use_datetime,
            )
            comparison_clause = f"!{equality_clause}"
        elif comparison.operator_name == GREATER_THAN.name:
            value_literal = self._render_value_operand(
                comparison.values[0],
                variable_name="value_0",
                vars_payload=vars_payload,
                use_datetime=use_datetime,
            )
            comparison_clause = f"({value_reference} > {value_literal})"
        elif comparison.operator_name == GREATER_THAN_OR_EQUAL.name:
            value_literal = self._render_value_operand(
                comparison.values[0],
                variable_name="value_0",
                vars_payload=vars_payload,
                use_datetime=use_datetime,
            )
            comparison_clause = f"({value_reference} >= {value_literal})"
        elif comparison.operator_name == LESS_THAN.name:
            value_literal = self._render_value_operand(
                comparison.values[0],
                variable_name="value_0",
                vars_payload=vars_payload,
                use_datetime=use_datetime,
            )
            comparison_clause = f"({value_reference} < {value_literal})"
        elif comparison.operator_name == LESS_THAN_OR_EQUAL.name:
            value_literal = self._render_value_operand(
                comparison.values[0],
                variable_name="value_0",
                vars_payload=vars_payload,
                use_datetime=use_datetime,
            )
            comparison_clause = f"({value_reference} <= {value_literal})"
        elif comparison.operator_name == IN.name:
            comparison_clause = self._membership_comparison(
                value_reference,
                comparison.values,
                operator="==",
                join_operator="||",
                vars_payload=vars_payload,
                use_datetime=use_datetime,
            )
        elif comparison.operator_name == NOT_IN.name:
            comparison_clause = self._membership_comparison(
                value_reference,
                comparison.values,
                operator="!=",
                join_operator="&&",
                vars_payload=vars_payload,
                use_datetime=use_datetime,
            )
        elif comparison.operator_name == IS_NULL.name:
            comparison_clause = "(@ == null)"
        elif comparison.operator_name == LIKE.name:
            comparison_clause = self._regex_comparison(
                comparison.values[0],
                ignore_case=False,
            )
        elif comparison.operator_name == NOT_LIKE.name:
            comparison_clause = "!" + self._regex_comparison(
                comparison.values[0],
                ignore_case=False,
            )
        elif comparison.operator_name == IGNORE_CASE.name:
            comparison_clause = self._regex_comparison(
                comparison.values[0],
                ignore_case=True,
            )
        elif comparison.operator_name == IGNORE_CASE_LIKE.name:
            comparison_clause = self._regex_comparison(
                comparison.values[0],
                ignore_case=True,
            )
        elif comparison.operator_name == IGNORE_CASE_NOT_LIKE.name:
            comparison_clause = "!" + self._regex_comparison(
                comparison.values[0],
                ignore_case=True,
            )
        elif comparison.operator_name == BETWEEN.name:
            lower_literal = self._render_value_operand(
                comparison.values[0],
                variable_name="value_0",
                vars_payload=vars_payload,
                use_datetime=use_datetime,
            )
            upper_literal = self._render_value_operand(
                comparison.values[1],
                variable_name="value_1",
                vars_payload=vars_payload,
                use_datetime=use_datetime,
            )
            comparison_clause = (
                f"({value_reference} >= {lower_literal}"
                f" && {value_reference} <= {upper_literal})"
            )
        elif comparison.operator_name == NOT_BETWEEN.name:
            lower_literal = self._render_value_operand(
                comparison.values[0],
                variable_name="value_0",
                vars_payload=vars_payload,
                use_datetime=use_datetime,
            )
            upper_literal = self._render_value_operand(
                comparison.values[1],
                variable_name="value_1",
                vars_payload=vars_payload,
                use_datetime=use_datetime,
            )
            comparison_clause = (
                f"({value_reference} < {lower_literal}"
                f" || {value_reference} > {upper_literal})"
            )
        else:
            raise SQLAlchemyORMError(
                f"Unsupported JSON operator {comparison.operator_name!r}."
            )
        return _JSONPathFilterCall(
            json_path_expression=f"{target_path} ? {comparison_clause}",
            use_timezone_function=use_timezone_function,
            path_exists_tz_function=options.path_exists_tz_function,
            vars_payload=vars_payload,
        )

    def _equality_comparison(
        self,
        value: JSONScalarValue,
        *,
        variable_name: str,
        vars_payload: dict[str, Any],
        use_datetime: bool,
    ) -> str:
        """Builds equality or wildcard comparison for JSON values."""
        if value.python_type is str and "*" in str(value.value):
            return self._regex_comparison(
                value,
                ignore_case=False,
            )
        value_reference = (
            "@.datetime()"
            if use_datetime and self._is_datetime_value(value)
            else "@"
        )
        return (
            f"({value_reference} == "
            f"{self._render_value_operand(value, variable_name=variable_name, vars_payload=vars_payload, use_datetime=use_datetime)})"
        )

    def _regex_comparison(
        self,
        value: JSONScalarValue,
        *,
        ignore_case: bool,
    ) -> str:
        """Builds a jsonpath like_regex comparison."""
        if value.python_type is not str:
            raise SQLAlchemyORMError(
                "LIKE-style JSON operators require string values."
            )
        normalized = str(value.value)
        if "*" not in normalized:
            normalized = f"*{normalized}*"
        pattern = re.escape(normalized).replace(r"\*", ".*")
        literal = json.dumps(pattern)
        if ignore_case:
            return f'(@ like_regex {literal} flag "i")'
        return f"(@ like_regex {literal})"

    def _membership_comparison(
        self,
        value_reference: str,
        values: tuple[JSONScalarValue, ...],
        *,
        operator: str,
        join_operator: str,
        vars_payload: dict[str, Any],
        use_datetime: bool,
    ) -> str:
        """Builds one JSON membership comparison clause."""
        comparisons = (
            (
                f"({value_reference} {operator} "
                f"{self._render_value_operand(value, variable_name=f'value_{index}', vars_payload=vars_payload, use_datetime=use_datetime)})"
            )
            for index, value in enumerate(values)
        )
        return "(" + f" {join_operator} ".join(comparisons) + ")"

    def _render_value_operand(
        self,
        value: JSONScalarValue,
        *,
        variable_name: str,
        vars_payload: dict[str, Any],
        use_datetime: bool,
    ) -> str:
        """Builds one JSON value operand for PostgreSQL jsonpath."""
        if value.python_type in (dict, list):
            vars_payload[variable_name] = value.value
            if use_datetime and self._is_datetime_value(value):
                return f"${variable_name}.datetime()"
            return f"${variable_name}"
        if use_datetime and self._is_datetime_value(value):
            return f'"{value.value}".datetime()'
        return value.json_literal

    def _is_datetime_value(self, value: JSONScalarValue) -> bool:
        """Returns whether a value is a supported ISO temporal string."""
        if value.python_type is not str:
            return False
        normalized = str(value.value)
        return (
            _ISO_DATE_TIME_PATTERN.fullmatch(normalized) is not None
            or _ISO_DATE_PATTERN.fullmatch(normalized) is not None
            or _ISO_TIME_PATTERN.fullmatch(normalized) is not None
            or self._is_timezone_datetime_value(value)
        )

    def _is_timezone_datetime_value(self, value: JSONScalarValue) -> bool:
        """Returns whether a value is a timezone-aware ISO temporal string."""
        if value.python_type is not str:
            return False
        normalized = str(value.value)
        return (
            _ISO_DATE_TIME_PATTERN_TZ.fullmatch(normalized) is not None
            or _ISO_TIME_PATTERN_TZ.fullmatch(normalized) is not None
        )


class _JSONPathFilterCall(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
):
    """Represents one PostgreSQL JSON path filter call."""

    json_path_expression: str
    use_timezone_function: bool
    path_exists_tz_function: str
    vars_payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        """Normalizes vars payload into an immutable mapping."""
        object.__setattr__(
            self,
            "vars_payload",
            MappingProxyType(dict(self.vars_payload)),
        )
