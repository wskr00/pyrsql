"""Sort translation for SQLAlchemy."""

from typing import Any
from typing import cast

import sqlalchemy as sa
from sqlalchemy.sql.elements import ColumnElement

from pyrsql.backends.sqlalchemy.json_support import SQLAlchemyJSONSupport
from pyrsql.backends.sqlalchemy.resolver import SQLAlchemyPathResolver
from pyrsql.backends.sqlalchemy.types import SQLAlchemyJoinPlan
from pyrsql.core.options import SortOptions
from pyrsql.selector.semantic import SemanticColumnSelector
from pyrsql.selector.semantic import SemanticLiteralSelector
from pyrsql.selector.semantic import SemanticSelector
from pyrsql.sorting.ast import SortDirection
from pyrsql.sorting.semantic import SemanticSortField


class SQLAlchemySortTranslator:
    """Translates semantic sort fields to SQLAlchemy order clauses."""

    def __init__(
        self,
        *,
        path_resolver: SQLAlchemyPathResolver | None = None,
        json_support: SQLAlchemyJSONSupport | None = None,
    ) -> None:
        self._path_resolver = path_resolver or SQLAlchemyPathResolver()
        self._json_support = json_support or SQLAlchemyJSONSupport()

    def translate(
        self,
        model: type[Any],
        fields: tuple[SemanticSortField, ...],
        *,
        options: SortOptions | None = None,
    ) -> tuple[
        tuple[SQLAlchemyJoinPlan, ...],
        tuple[ColumnElement[Any], ...],
    ]:
        """Translates semantic sort fields for a mapped model."""
        joins: list[Any] = []
        order_clauses: list[ColumnElement[Any]] = []
        for field in fields:
            selector_joins, expression, python_type = self._translate_selector(
                model,
                field.selector,
                options=options,
            )
            joins.extend(selector_joins)
            order_clauses.append(
                self._build_order_clause(
                    expression,
                    python_type,
                    field,
                )
            )
        return tuple(joins), tuple(order_clauses)

    def _translate_selector(
        self,
        model: type[Any],
        selector: SemanticSelector,
        *,
        options: SortOptions | None = None,
    ) -> tuple[
        tuple[SQLAlchemyJoinPlan, ...],
        ColumnElement[Any],
        type[Any] | None,
    ]:
        """Translates a semantic selector recursively."""
        if isinstance(selector, SemanticColumnSelector):
            resolved_path = self._path_resolver.resolve(
                model,
                selector.field_path,
                field_policy=options.field_policy if options else None,
            )
            return (
                resolved_path.joins,
                self._resolve_column_expression(resolved_path),
                str if resolved_path.is_json else resolved_path.python_type,
            )
        if isinstance(selector, SemanticLiteralSelector):
            python_type = (
                type(selector.value)
                if selector.value is not None
                else None
            )
            return (), sa.literal(selector.value), python_type

        joins: list[Any] = []
        argument_expressions: list[ColumnElement[Any]] = []
        argument_types: list[type[Any] | None] = []
        for argument in selector.arguments:
            argument_joins, argument_expression, argument_type = (
                self._translate_selector(
                    model,
                    argument,
                    options=options,
                )
            )
            joins.extend(argument_joins)
            argument_expressions.append(argument_expression)
            argument_types.append(argument_type)
        function_expression = getattr(sa.func, selector.function_name)(
            *argument_expressions
        )
        return (
            tuple(joins),
            cast(ColumnElement[Any], function_expression),
            self._infer_function_python_type(
                selector.function_name,
                tuple(argument_types),
            ),
        )

    def _resolve_column_expression(
        self,
        resolved_path: Any,
    ) -> ColumnElement[Any]:
        """Builds the effective SQL expression for a resolved path."""
        base_expression = cast(ColumnElement[Any], resolved_path.leaf_attribute)
        if not resolved_path.is_json:
            return base_expression
        return self._json_support.build_sort_expression(
            base_expression,
            resolved_path.json_path,
        )

    def _build_order_clause(
        self,
        expression: ColumnElement[Any],
        python_type: type[Any] | None,
        field: SemanticSortField,
    ) -> ColumnElement[Any]:
        """Builds an ORDER BY clause for a resolved sort field."""
        if field.ignore_case and self._is_string_type(python_type):
            expression = cast(ColumnElement[Any], sa.func.lower(expression))
        if field.direction is SortDirection.DESCENDING:
            return cast(ColumnElement[Any], expression.desc())
        return cast(ColumnElement[Any], expression.asc())

    def _is_string_type(self, python_type: type[Any] | None) -> bool:
        """Returns whether the resolved Python type is string-compatible."""
        if python_type is None:
            return False
        return issubclass(python_type, str)

    def _infer_function_python_type(
        self,
        function_name: str,
        argument_types: tuple[type[Any] | None, ...],
    ) -> type[Any] | None:
        """Infers the Python type for common SQL functions."""
        normalized_name = function_name.lower()
        if normalized_name in {"lower", "upper", "concat"}:
            return str
        if normalized_name == "coalesce":
            for argument_type in argument_types:
                if argument_type is not None:
                    return argument_type
        return None
