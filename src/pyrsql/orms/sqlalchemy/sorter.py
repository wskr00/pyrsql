"""Bound sort IR lowering for SQLAlchemy."""

from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.sql.elements import ColumnElement

from pyrsql.core.options import SortOptions
from pyrsql.ir.query import (
    BoundField,
    BoundFunction,
    BoundLiteral,
    BoundSelectorNode,
)
from pyrsql.ir.sort import BoundSort, BoundSortField
from pyrsql.orms.sqlalchemy.json_path import (
    SQLAlchemyJSONPathExpressionBuilder,
)
from pyrsql.orms.sqlalchemy.resolver import SQLAlchemyPathResolver
from pyrsql.orms.sqlalchemy.type_inference import (
    infer_sql_function_python_type,
    is_string_python_type,
)
from pyrsql.orms.sqlalchemy.types import (
    SQLAlchemyJoinPlan,
    SQLAlchemyResolvedPath,
)
from pyrsql.sorting.ast import SortDirection


class SQLAlchemySortTranslator:
    """Lowers bound sort IR to SQLAlchemy order clauses."""

    __slots__ = ("_path_resolver", "_json_path_builder")

    def __init__(
        self,
        *,
        path_resolver: SQLAlchemyPathResolver | None = None,
        json_path_builder: SQLAlchemyJSONPathExpressionBuilder | None = None,
    ) -> None:
        self._path_resolver = path_resolver or SQLAlchemyPathResolver()
        self._json_path_builder = (
            json_path_builder or SQLAlchemyJSONPathExpressionBuilder()
        )

    def translate(
        self,
        model: type[Any],
        sort_plan: BoundSort,
        *,
        options: SortOptions | None = None,
    ) -> tuple[
        tuple[SQLAlchemyJoinPlan, ...],
        tuple[ColumnElement[Any], ...],
    ]:
        """Lowers bound sort IR for a mapped model."""
        joins: list[SQLAlchemyJoinPlan] = []
        order_clauses: list[ColumnElement[Any]] = []
        for field in sort_plan.fields:
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
        selector: BoundSelectorNode,
        *,
        options: SortOptions | None = None,
    ) -> tuple[
        tuple[SQLAlchemyJoinPlan, ...],
        ColumnElement[Any],
        type[Any] | None,
    ]:
        """Lowers one bound selector recursively."""
        if isinstance(selector, BoundField):
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
        if isinstance(selector, BoundLiteral):
            python_type = (
                type(selector.value) if selector.value is not None else None
            )
            return (), sa.literal(selector.value), python_type

        if not isinstance(selector, BoundFunction):
            raise TypeError("Expected BoundFunction")
        joins: list[SQLAlchemyJoinPlan] = []
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
        function_expression = getattr(
            sa.func,
            selector.function_name,
        )(*argument_expressions)
        return (
            tuple(joins),
            cast(ColumnElement[Any], function_expression),
            infer_sql_function_python_type(
                selector.function_name,
                tuple(argument_types),
            ),
        )

    def _resolve_column_expression(
        self,
        resolved_path: SQLAlchemyResolvedPath,
    ) -> ColumnElement[Any]:
        """Builds the effective SQL expression for a resolved path."""
        base_expression = resolved_path.leaf_attribute
        if not resolved_path.is_json:
            return base_expression
        return self._json_path_builder.build_sort_expression(
            base_expression,
            resolved_path.json_path,
        )

    def _build_order_clause(
        self,
        expression: ColumnElement[Any],
        python_type: type[Any] | None,
        field: BoundSortField,
    ) -> ColumnElement[Any]:
        """Builds an ORDER BY clause for a resolved sort field."""
        if field.ignore_case and is_string_python_type(python_type):
            expression = cast(ColumnElement[Any], sa.func.lower(expression))
        if field.direction is SortDirection.DESCENDING:
            return cast(ColumnElement[Any], expression.desc())
        return cast(ColumnElement[Any], expression.asc())
