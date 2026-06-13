"""JSON path expression building for the SQLAlchemy orm."""

from __future__ import annotations

import re
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, cast

import msgspec
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from pyrsql.core.json.options import (
    DEFAULT_JSON_OPTIONS,
    JSONSortScalarType,
)
from pyrsql.orms.sqlalchemy.errors import (
    SQLAlchemyJSONSupportError,
    SQLAlchemyORMError,
)
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

if TYPE_CHECKING:
    from collections.abc import Mapping

    from sqlalchemy.sql.elements import ColumnElement

    from pyrsql.core.json.options import (
        JSONOptions,
    )
    from pyrsql.core.json.path import JSONPath
    from pyrsql.core.json.query import JSONPathComparison
    from pyrsql.core.json.values import JSONScalarValue

_ISO_DATE_TIME_PATTERN_TZ = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$",
)
_ISO_TIME_PATTERN_TZ = re.compile(
    r"^\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$",
)
_ISO_DATE_TIME_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$",
)
_ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ISO_TIME_PATTERN = re.compile(r"^\d{2}:\d{2}:\d{2}(\.\d+)?$")
_JSON_ENCODER = msgspec.json.Encoder()
_ORDERED_COMPARISON_OPERATORS = MappingProxyType(
    {
        GREATER_THAN.name: ">",
        GREATER_THAN_OR_EQUAL.name: ">=",
        LESS_THAN.name: "<",
        LESS_THAN_OR_EQUAL.name: "<=",
    },
)
_IGNORE_CASE_JSON_OPERATORS = frozenset(
    {
        IGNORE_CASE.name,
        IGNORE_CASE_LIKE.name,
        IGNORE_CASE_NOT_LIKE.name,
    },
)
_NEGATED_REGEX_JSON_OPERATORS = frozenset(
    {
        NOT_LIKE.name,
        IGNORE_CASE_NOT_LIKE.name,
    },
)


class SQLAlchemyJSONPathExpressionBuilder:
    """Builds PostgreSQL JSON path expressions for SQLAlchemy."""

    __slots__ = ()

    _DIRECT_DOCUMENT_OPERATORS = frozenset(
        (
            EQUAL.name,
            NOT_EQUAL.name,
            IN.name,
            NOT_IN.name,
            IS_NULL.name,
            NOT_NULL.name,
        ),
    )

    def supports_document_predicate(
        self,
        comparison: JSONPathComparison,
    ) -> bool:
        """Returns whether a whole-document predicate should skip jsonpath."""
        return (
            comparison.path.is_root
            and comparison.operator_name in self._DIRECT_DOCUMENT_OPERATORS
        )

    def build_document_filter_expression(
        self,
        column: ColumnElement[Any],
        comparison: JSONPathComparison,
    ) -> ColumnElement[bool]:
        """Builds a direct whole-document JSONB predicate.

        Returns:
            A direct JSONB predicate for the whole document.

        Raises:
            SQLAlchemyJSONSupportError: If the operator is unsupported for
                whole-document comparisons.
        """
        jsonb_column = cast(
            "ColumnElement[Any]",
            sa.cast(column, postgresql.JSONB),
        )
        match comparison.operator_name:
            case EQUAL.name:
                return jsonb_column == self._jsonb_value_literal(
                    comparison.values[0],
                )
            case NOT_EQUAL.name:
                return jsonb_column != self._jsonb_value_literal(
                    comparison.values[0],
                )
            case IN.name:
                return cast(
                    "ColumnElement[bool]",
                    jsonb_column.in_(
                        tuple(
                            self._jsonb_value_literal(value)
                            for value in comparison.values
                        ),
                    ),
                )
            case NOT_IN.name:
                return cast(
                    "ColumnElement[bool]",
                    jsonb_column.not_in(
                        tuple(
                            self._jsonb_value_literal(value)
                            for value in comparison.values
                        ),
                    ),
                )
            case IS_NULL.name:
                return jsonb_column == self._jsonb_null_literal()
            case NOT_NULL.name:
                return jsonb_column != self._jsonb_null_literal()
            case _:
                raise SQLAlchemyJSONSupportError(
                    "Unsupported whole-document JSON predicate "
                    f"{comparison.operator_name!r}.",
                )

    def build_filter_expression(
        self,
        column: ColumnElement[Any],
        comparison: JSONPathComparison,
        *,
        options: JSONOptions | None = None,
    ) -> ColumnElement[bool]:
        """Builds a PostgreSQL JSONB path-exists predicate.

        Returns:
            A PostgreSQL ``jsonb_path_exists`` predicate.
        """
        active_options = DEFAULT_JSON_OPTIONS if options is None else options
        function_call = self._build_filter_call(
            comparison,
            options=active_options,
        )
        jsonb_column = cast(
            "ColumnElement[Any]",
            sa.cast(column, postgresql.JSONB),
        )
        json_path_literal = self._jsonpath_literal(
            function_call.json_path_expression,
        )
        vars_payload = self._jsonpath_vars_payload(function_call.vars_payload)
        function_name = (
            function_call.path_exists_tz_function
            if function_call.use_timezone_function
            else active_options.path_exists_function
        )
        function_expression = getattr(sa.func, function_name)(
            jsonb_column,
            json_path_literal,
            vars_payload,
        )
        return cast("ColumnElement[bool]", function_expression)

    @staticmethod
    def _jsonpath_literal(expression: str) -> ColumnElement[Any]:
        """Builds one JSONPATH-typed literal for PostgreSQL predicates.

        Returns:
            A PostgreSQL ``JSONPATH`` literal expression.
        """
        return cast(
            "ColumnElement[Any]",
            sa.cast(sa.literal(expression), postgresql.JSONPATH),
        )

    @staticmethod
    def _jsonpath_vars_payload(
        vars_payload: Mapping[str, Any],
    ) -> ColumnElement[Any]:
        """Builds the JSONB vars payload passed to PostgreSQL jsonpath funcs.

        Returns:
            A JSONB-typed vars payload expression.
        """
        return cast(
            "ColumnElement[Any]",
            sa.cast(
                sa.literal(dict(vars_payload), type_=postgresql.JSONB),
                postgresql.JSONB,
            ),
        )

    @staticmethod
    def _jsonb_value_literal(
        value: JSONScalarValue,
    ) -> ColumnElement[Any]:
        """Builds one JSONB-typed literal from a normalized JSON value.

        Returns:
            A JSONB-typed literal expression.
        """
        return cast(
            "ColumnElement[Any]",
            sa.cast(sa.literal(value.json_literal), postgresql.JSONB),
        )

    @staticmethod
    def _jsonb_null_literal() -> ColumnElement[Any]:
        """Builds one JSONB literal representing JSON null.

        Returns:
            A JSONB literal that represents JSON null.
        """
        return cast(
            "ColumnElement[Any]",
            sa.cast(sa.literal("null"), postgresql.JSONB),
        )

    def build_sort_expression(
        self,
        column: ColumnElement[Any],
        json_path: JSONPath,
        *,
        field_path: str,
        options: JSONOptions | None = None,
    ) -> ColumnElement[Any]:
        """Builds a PostgreSQL JSON path extraction expression for sort.

        Returns:
            The SQLAlchemy expression used for JSON sorting.
        """
        active_options = DEFAULT_JSON_OPTIONS if options is None else options
        jsonb_column = cast(
            "ColumnElement[Any]",
            sa.cast(column, postgresql.JSONB),
        )
        sort_type = active_options.sort_field_types.get(
            field_path,
            JSONSortScalarType.TEXT,
        )
        if json_path.is_root:
            return self._build_root_sort_expression(
                jsonb_column,
                field_path=field_path,
                sort_type=sort_type,
                has_explicit_config=(
                    field_path in active_options.sort_field_types
                ),
            )
        text_expression = cast(
            "ColumnElement[Any]",
            jsonb_column[json_path.segments].as_string(),
        )
        return self._cast_sort_expression(
            text_expression,
            sort_type=sort_type,
        )

    @staticmethod
    def _build_root_sort_expression(
        jsonb_column: ColumnElement[Any],
        *,
        field_path: str,
        sort_type: JSONSortScalarType,
        has_explicit_config: bool,
    ) -> ColumnElement[Any]:
        """Builds a root JSON document sort expression.

        Returns:
            A SQLAlchemy expression for sorting whole JSON documents.

        Raises:
            SQLAlchemyJSONSupportError: If root JSON sorting is not explicitly
                configured or is not text-based.
        """
        if not has_explicit_config:
            raise SQLAlchemyJSONSupportError(
                "Sorting by a whole JSON document requires an explicit "
                f"json sort type for field {field_path!r}.",
            )
        if sort_type is not JSONSortScalarType.TEXT:
            raise SQLAlchemyJSONSupportError(
                "Whole-document JSON sorting currently supports only "
                f"text semantics for field {field_path!r}.",
            )
        return cast("ColumnElement[Any]", sa.cast(jsonb_column, sa.Text()))

    @staticmethod
    def _cast_sort_expression(
        expression: ColumnElement[Any],
        *,
        sort_type: JSONSortScalarType,
    ) -> ColumnElement[Any]:
        """Applies one configured scalar cast to a JSON sort expression.

        Returns:
            The cast SQLAlchemy expression.

        Raises:
            SQLAlchemyJSONSupportError: If the configured sort type is
                unsupported.
        """
        match sort_type:
            case JSONSortScalarType.TEXT:
                return expression
            case JSONSortScalarType.INTEGER:
                target_type: Any = sa.Integer()
            case JSONSortScalarType.FLOAT:
                target_type = sa.Float()
            case JSONSortScalarType.NUMERIC:
                target_type = sa.Numeric()
            case JSONSortScalarType.BOOLEAN:
                target_type = sa.Boolean()
            case JSONSortScalarType.DATE:
                target_type = sa.Date()
            case JSONSortScalarType.TIME:
                target_type = sa.Time()
            case JSONSortScalarType.DATETIME:
                target_type = sa.DateTime(timezone=False)
            case JSONSortScalarType.DATETIME_TZ:
                target_type = sa.DateTime(timezone=True)
            case _:
                raise SQLAlchemyJSONSupportError(
                    f"Unsupported JSON sort scalar type {sort_type!r}.",
                )
        return cast("ColumnElement[Any]", sa.cast(expression, target_type))

    def _build_filter_call(
        self,
        comparison: JSONPathComparison,
        *,
        options: JSONOptions,
    ) -> _JSONPathFilterCall:
        """Builds the function call payload for one jsonpath predicate.

        Returns:
            The rendered JSON path filter call payload.

        Raises:
            SQLAlchemyORMError: If the operator cannot be rendered as JSON
                path.
        """
        target_path = comparison.path.to_postgresql_jsonpath()
        use_datetime = options.use_datetime
        has_datetime_value = False
        use_timezone_function = False
        if use_datetime:
            for value in comparison.values:
                if self._is_timezone_datetime_value(value):
                    has_datetime_value = True
                    use_timezone_function = True
                    break
                if self._is_datetime_value(value):
                    has_datetime_value = True
        vars_payload: dict[str, Any] = {}
        value_reference = (
            "@.datetime()" if use_datetime and has_datetime_value else "@"
        )
        match comparison.operator_name:
            case NOT_NULL.name:
                comparison_clause = "(@ != null)"
            case EQUAL.name:
                comparison_clause = self._equality_comparison(
                    comparison.values[0],
                    variable_name="value_0",
                    vars_payload=vars_payload,
                    use_datetime=use_datetime,
                )
            case NOT_EQUAL.name:
                equality_clause = self._equality_comparison(
                    comparison.values[0],
                    variable_name="value_0",
                    vars_payload=vars_payload,
                    use_datetime=use_datetime,
                )
                comparison_clause = f"!{equality_clause}"
            case (
                GREATER_THAN.name
                | GREATER_THAN_OR_EQUAL.name
                | LESS_THAN.name
                | LESS_THAN_OR_EQUAL.name
            ):
                operator = _ORDERED_COMPARISON_OPERATORS[
                    comparison.operator_name
                ]
                value_literal = self._render_value_operand(
                    comparison.values[0],
                    variable_name="value_0",
                    vars_payload=vars_payload,
                    use_datetime=use_datetime,
                )
                comparison_clause = (
                    f"({value_reference} {operator} {value_literal})"
                )
            case IN.name:
                comparison_clause = self._membership_comparison(
                    value_reference,
                    comparison.values,
                    operator="==",
                    join_operator="||",
                    vars_payload=vars_payload,
                    use_datetime=use_datetime,
                )
            case NOT_IN.name:
                comparison_clause = self._membership_comparison(
                    value_reference,
                    comparison.values,
                    operator="!=",
                    join_operator="&&",
                    vars_payload=vars_payload,
                    use_datetime=use_datetime,
                )
            case IS_NULL.name:
                comparison_clause = "(@ == null)"
            case (
                LIKE.name
                | NOT_LIKE.name
                | IGNORE_CASE.name
                | IGNORE_CASE_LIKE.name
                | IGNORE_CASE_NOT_LIKE.name
            ):
                ignore_case = (
                    comparison.operator_name in _IGNORE_CASE_JSON_OPERATORS
                )
                comparison_clause = self._regex_comparison(
                    comparison.values[0],
                    ignore_case=ignore_case,
                )
                if comparison.operator_name in _NEGATED_REGEX_JSON_OPERATORS:
                    comparison_clause = f"!{comparison_clause}"
            case BETWEEN.name | NOT_BETWEEN.name:
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
                if comparison.operator_name == BETWEEN.name:
                    comparison_clause = (
                        f"({value_reference} >= {lower_literal}"
                        f" && {value_reference} <= {upper_literal})"
                    )
                else:
                    comparison_clause = (
                        f"({value_reference} < {lower_literal}"
                        f" || {value_reference} > {upper_literal})"
                    )
            case _:
                raise SQLAlchemyORMError(
                    f"Unsupported JSON operator {comparison.operator_name!r}.",
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
        """Builds equality or wildcard comparison for JSON values.

        Returns:
            A JSON path comparison clause.
        """
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
            f"{self._render_value_operand(value, variable_name=variable_name, vars_payload=vars_payload, use_datetime=use_datetime)})"  # noqa: E501
        )

    @staticmethod
    def _regex_comparison(
        value: JSONScalarValue,
        *,
        ignore_case: bool,
    ) -> str:
        """Builds a jsonpath like_regex comparison.

        Returns:
            A JSON path regex comparison clause.

        Raises:
            SQLAlchemyORMError: If the value is not a string.
        """
        if value.python_type is not str:
            raise SQLAlchemyORMError(
                "LIKE-style JSON operators require string values.",
            )
        normalized = str(value.value)
        if "*" not in normalized:
            normalized = f"*{normalized}*"
        pattern = re.escape(normalized).replace(r"\*", ".*")
        literal = _JSON_ENCODER.encode(pattern).decode()
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
        """Builds one JSON membership comparison clause.

        Returns:
            A JSON path membership comparison clause.
        """
        comparisons = (
            (
                f"({value_reference} {operator} "
                f"{self._render_value_operand(value, variable_name=f'value_{index}', vars_payload=vars_payload, use_datetime=use_datetime)})"  # noqa: E501
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
        """Builds one JSON value operand for PostgreSQL jsonpath.

        Returns:
            A JSON path operand string.
        """
        if value.python_type in {dict, list}:
            vars_payload[variable_name] = value.value
            if use_datetime and self._is_datetime_value(value):
                return f"${variable_name}.datetime()"
            return f"${variable_name}"
        if use_datetime and self._is_datetime_value(value):
            return f'"{value.value}".datetime()'
        return value.json_literal

    def _is_datetime_value(self, value: JSONScalarValue) -> bool:
        """Returns whether a value is a supported ISO temporal string.

        Returns:
            ``True`` when the value is a supported ISO temporal string.
        """
        if value.python_type is not str:
            return False
        normalized = str(value.value)
        return (
            _ISO_DATE_TIME_PATTERN.fullmatch(normalized) is not None
            or _ISO_DATE_PATTERN.fullmatch(normalized) is not None
            or _ISO_TIME_PATTERN.fullmatch(normalized) is not None
            or self._is_timezone_datetime_value(value)
        )

    @staticmethod
    def _is_timezone_datetime_value(value: JSONScalarValue) -> bool:
        """Returns whether a value is a timezone-aware ISO temporal string.

        Returns:
            ``True`` when the value is a timezone-aware ISO temporal string.
        """
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
