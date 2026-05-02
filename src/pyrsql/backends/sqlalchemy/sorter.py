"""Sort translation for SQLAlchemy."""

from typing import Any
from typing import cast

import sqlalchemy as sa
from sqlalchemy.sql.elements import ColumnElement

from pyrsql.backends.sqlalchemy.resolver import SQLAlchemyPathResolver
from pyrsql.backends.sqlalchemy.types import SQLAlchemyJoinPlan
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
    ) -> None:
        self._path_resolver = path_resolver or SQLAlchemyPathResolver()

    def translate(
        self,
        model: type[Any],
        fields: tuple[SemanticSortField, ...],
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
            )
            return (
                resolved_path.joins,
                cast(ColumnElement[Any], resolved_path.leaf_attribute),
                resolved_path.python_type,
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
                self._translate_selector(model, argument)
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
