"""JSON path expression building for the SQLAlchemy backend."""

import json
import re
from dataclasses import dataclass
from typing import Any
from typing import cast

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.elements import ColumnElement

from pyrsql.backends.sqlalchemy.errors import SQLAlchemyBackendError
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

_INTEGER_PATTERN = re.compile(r"^-?\d+$")
_FLOAT_PATTERN = re.compile(r"^-?\d+\.\d+$")


@dataclass(frozen=True, slots=True)
class JSONScalarValue:
    """Represents one inferred JSON scalar value."""

    value: Any
    json_path_literal: str
    python_type: type[Any] | None


class SQLAlchemyJSONPathExpressionBuilder:
    """Builds PostgreSQL JSON path expressions for SQLAlchemy."""

    def build_filter_expression(
        self,
        column: ColumnElement[Any],
        json_path: tuple[str, ...],
        operator_name: str,
        raw_arguments: tuple[tuple[str, bool], ...],
    ) -> ColumnElement[bool]:
        """Builds a PostgreSQL jsonb_path_exists predicate."""
        normalized_values = tuple(
            self._normalize_argument(raw_value, quoted=quoted)
            for raw_value, quoted in raw_arguments
        )
        json_path_expression = self._build_json_path_expression(
            json_path,
            operator_name,
            normalized_values,
        )
        jsonb_column = cast(
            ColumnElement[Any],
            sa.cast(column, postgresql.JSONB),
        )
        return cast(
            ColumnElement[bool],
            sa.func.jsonb_path_exists(
                jsonb_column,
                sa.literal(json_path_expression),
            ),
        )

    def build_sort_expression(
        self,
        column: ColumnElement[Any],
        json_path: tuple[str, ...],
    ) -> ColumnElement[Any]:
        """Builds a PostgreSQL text extraction expression for sort."""
        jsonb_column = cast(
            ColumnElement[Any],
            sa.cast(column, postgresql.JSONB),
        )
        if not json_path:
            return jsonb_column
        arguments: list[ColumnElement[Any]] = [jsonb_column]
        arguments.extend(sa.literal(segment) for segment in json_path)
        return cast(
            ColumnElement[Any],
            sa.func.jsonb_extract_path_text(*arguments),
        )

    def _build_json_path_expression(
        self,
        json_path: tuple[str, ...],
        operator_name: str,
        values: tuple[JSONScalarValue, ...],
    ) -> str:
        """Builds one jsonpath predicate expression."""
        target_path = "$" if not json_path else "$." + ".".join(json_path)
        value_reference = "@"
        if operator_name == NOT_NULL.name:
            comparison = "(@ != null)"
        elif operator_name == EQUAL.name:
            comparison = self._equality_comparison(values[0])
        elif operator_name == NOT_EQUAL.name:
            comparison = f"!{self._equality_comparison(values[0])}"
        elif operator_name == GREATER_THAN.name:
            comparison = f"(@ > {values[0].json_path_literal})"
        elif operator_name == GREATER_THAN_OR_EQUAL.name:
            comparison = f"(@ >= {values[0].json_path_literal})"
        elif operator_name == LESS_THAN.name:
            comparison = f"(@ < {values[0].json_path_literal})"
        elif operator_name == LESS_THAN_OR_EQUAL.name:
            comparison = f"(@ <= {values[0].json_path_literal})"
        elif operator_name == IN.name:
            comparison = "(" + " || ".join(
                f"(@ == {value.json_path_literal})"
                for value in values
            ) + ")"
        elif operator_name == NOT_IN.name:
            comparison = "(" + " && ".join(
                f"(@ != {value.json_path_literal})"
                for value in values
            ) + ")"
        elif operator_name == IS_NULL.name:
            comparison = "(@ == null)"
        elif operator_name == LIKE.name:
            comparison = self._regex_comparison(values[0], ignore_case=False)
        elif operator_name == NOT_LIKE.name:
            comparison = "!" + self._regex_comparison(
                values[0],
                ignore_case=False,
            )
        elif operator_name == IGNORE_CASE.name:
            comparison = self._regex_comparison(values[0], ignore_case=True)
        elif operator_name == IGNORE_CASE_LIKE.name:
            comparison = self._regex_comparison(values[0], ignore_case=True)
        elif operator_name == IGNORE_CASE_NOT_LIKE.name:
            comparison = "!" + self._regex_comparison(
                values[0],
                ignore_case=True,
            )
        elif operator_name == BETWEEN.name:
            comparison = (
                f"({value_reference} >= {values[0].json_path_literal} && "
                f"{value_reference} <= {values[1].json_path_literal})"
            )
        elif operator_name == NOT_BETWEEN.name:
            comparison = (
                f"({value_reference} < {values[0].json_path_literal} || "
                f"{value_reference} > {values[1].json_path_literal})"
            )
        else:
            raise SQLAlchemyBackendError(
                f"Unsupported JSON operator {operator_name!r}."
            )
        return f"{target_path} ? {comparison}"

    def _equality_comparison(self, value: JSONScalarValue) -> str:
        """Builds equality or wildcard comparison for JSON values."""
        if value.python_type is str and "*" in str(value.value):
            return self._regex_comparison(value, ignore_case=False)
        return f"(@ == {value.json_path_literal})"

    def _regex_comparison(
        self,
        value: JSONScalarValue,
        *,
        ignore_case: bool,
    ) -> str:
        """Builds a jsonpath like_regex comparison."""
        if value.python_type is not str:
            raise SQLAlchemyBackendError(
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

    def _normalize_argument(
        self,
        raw_value: str,
        *,
        quoted: bool,
    ) -> JSONScalarValue:
        """Infers one JSON scalar literal from an RSQL argument."""
        if quoted:
            parsed_json = self._try_parse_json(raw_value)
            if parsed_json is not None:
                return self._from_python_value(parsed_json)
            return self._from_python_value(raw_value)
        lowered = raw_value.lower()
        if lowered == "true":
            return self._from_python_value(True)
        if lowered == "false":
            return self._from_python_value(False)
        if lowered == "null":
            return self._from_python_value(None)
        if _INTEGER_PATTERN.fullmatch(raw_value):
            return self._from_python_value(int(raw_value))
        if _FLOAT_PATTERN.fullmatch(raw_value):
            return self._from_python_value(float(raw_value))
        return self._from_python_value(raw_value)

    def _from_python_value(self, value: Any) -> JSONScalarValue:
        """Creates a JSONScalarValue from a Python value."""
        return JSONScalarValue(
            value=value,
            json_path_literal=json.dumps(value),
            python_type=type(value) if value is not None else None,
        )

    def _try_parse_json(self, raw_value: str) -> Any | None:
        """Parses JSON structures from quoted RSQL arguments when possible."""
        try:
            parsed = json.loads(raw_value)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, str):
            return None
        return parsed
