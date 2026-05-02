"""JSON path expression building for the SQLAlchemy orm."""

import json
import re
from dataclasses import dataclass
from typing import Any
from typing import cast

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.elements import ColumnElement

from pyrsql.orms.sqlalchemy.errors import SQLAlchemyORMError
from pyrsql.core.json.options import JSONOptions
from pyrsql.core.json.path import JSONPath
from pyrsql.core.json.query import JSONPathComparison
from pyrsql.core.json.values import JSONScalarValue
from pyrsql.parsing.operators import BETWEEN
from pyrsql.parsing.operators import EQUAL
from pyrsql.parsing.operators import GREATER_THAN
from pyrsql.parsing.operators import GREATER_THAN_OR_EQUAL
from pyrsql.parsing.operators import IGNORE_CASE
from pyrsql.parsing.operators import IGNORE_CASE_LIKE
from pyrsql.parsing.operators import IGNORE_CASE_NOT_LIKE
from pyrsql.parsing.operators import IN
from pyrsql.parsing.operators import IS_NULL
from pyrsql.parsing.operators import LESS_THAN
from pyrsql.parsing.operators import LESS_THAN_OR_EQUAL
from pyrsql.parsing.operators import LIKE
from pyrsql.parsing.operators import NOT_BETWEEN
from pyrsql.parsing.operators import NOT_EQUAL
from pyrsql.parsing.operators import NOT_IN
from pyrsql.parsing.operators import NOT_LIKE
from pyrsql.parsing.operators import NOT_NULL

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
_DEFAULT_JSON_OPTIONS = JSONOptions()


class SQLAlchemyJSONPathExpressionBuilder:
    """Builds PostgreSQL JSON path expressions for SQLAlchemy."""

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
            options=options or _DEFAULT_JSON_OPTIONS,
        )
        jsonb_column = cast(
            ColumnElement[Any],
            sa.cast(column, postgresql.JSONB),
        )
        if function_call.use_timezone_function:
            function_expression = getattr(
                sa.func,
                function_call.path_exists_tz_function,
            )(
                jsonb_column,
                sa.literal(function_call.json_path_expression),
            )
            return cast(ColumnElement[bool], function_expression)
        if options and options.path_exists_function != "jsonb_path_exists":
            function_expression = getattr(
                sa.func,
                options.path_exists_function,
            )(
                jsonb_column,
                sa.literal(function_call.json_path_expression),
            )
            return cast(ColumnElement[bool], function_expression)
        return cast(
            ColumnElement[bool],
            jsonb_column.path_exists(
                sa.literal(function_call.json_path_expression)
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
        target_path = (
            "$"
            if comparison.path.is_root
            else "$." + comparison.path.to_dot_path()
        )
        use_datetime = options.use_datetime
        use_timezone_function = use_datetime and any(
            self._is_timezone_datetime_value(value)
            for value in comparison.values
        )
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
                use_datetime=use_datetime,
            )
        elif comparison.operator_name == NOT_EQUAL.name:
            equality_clause = self._equality_comparison(
                comparison.values[0],
                use_datetime=use_datetime,
            )
            comparison_clause = f"!{equality_clause}"
        elif comparison.operator_name == GREATER_THAN.name:
            value_literal = self._print_value(
                comparison.values[0],
                use_datetime=use_datetime,
            )
            comparison_clause = f"({value_reference} > {value_literal})"
        elif comparison.operator_name == GREATER_THAN_OR_EQUAL.name:
            value_literal = self._print_value(
                comparison.values[0],
                use_datetime=use_datetime,
            )
            comparison_clause = f"({value_reference} >= {value_literal})"
        elif comparison.operator_name == LESS_THAN.name:
            value_literal = self._print_value(
                comparison.values[0],
                use_datetime=use_datetime,
            )
            comparison_clause = f"({value_reference} < {value_literal})"
        elif comparison.operator_name == LESS_THAN_OR_EQUAL.name:
            value_literal = self._print_value(
                comparison.values[0],
                use_datetime=use_datetime,
            )
            comparison_clause = f"({value_reference} <= {value_literal})"
        elif comparison.operator_name == IN.name:
            comparison_clause = self._membership_comparison(
                value_reference,
                comparison.values,
                operator="==",
                join_operator="||",
                use_datetime=use_datetime,
            )
        elif comparison.operator_name == NOT_IN.name:
            comparison_clause = self._membership_comparison(
                value_reference,
                comparison.values,
                operator="!=",
                join_operator="&&",
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
            lower_literal = self._print_value(
                comparison.values[0],
                use_datetime=use_datetime,
            )
            upper_literal = self._print_value(
                comparison.values[1],
                use_datetime=use_datetime,
            )
            comparison_clause = (
                f"({value_reference} >= {lower_literal}"
                f" && {value_reference} <= {upper_literal})"
            )
        elif comparison.operator_name == NOT_BETWEEN.name:
            lower_literal = self._print_value(
                comparison.values[0],
                use_datetime=use_datetime,
            )
            upper_literal = self._print_value(
                comparison.values[1],
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
        )

    def _equality_comparison(
        self,
        value: JSONScalarValue,
        *,
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
            f"{self._print_value(value, use_datetime=use_datetime)})"
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
            return f"(@ like_regex {literal} flag \"i\")"
        return f"(@ like_regex {literal})"

    def _membership_comparison(
        self,
        value_reference: str,
        values: tuple[JSONScalarValue, ...],
        *,
        operator: str,
        join_operator: str,
        use_datetime: bool,
    ) -> str:
        """Builds one JSON membership comparison clause."""
        comparisons = (
            (
                f"({value_reference} {operator} "
                f"{self._print_value(value, use_datetime=use_datetime)})"
            )
            for value in values
        )
        return "(" + f" {join_operator} ".join(comparisons) + ")"

    def _print_value(
        self,
        value: JSONScalarValue,
        *,
        use_datetime: bool,
    ) -> str:
        """Prints one JSON value for PostgreSQL jsonpath expressions."""
        if use_datetime and self._is_datetime_value(value):
            return f"\"{value.value}\".datetime()"
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


@dataclass(frozen=True, slots=True)
class _JSONPathFilterCall:
    """Represents one PostgreSQL JSON path filter call."""

    json_path_expression: str
    use_timezone_function: bool
    path_exists_tz_function: str
