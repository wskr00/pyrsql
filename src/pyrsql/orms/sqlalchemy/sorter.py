"""Bound sort IR lowering for SQLAlchemy."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Any, cast

import sqlalchemy as sa

from pyrsql.core.json.options import DEFAULT_JSON_OPTIONS, JSONSortScalarType
from pyrsql.orms.sqlalchemy.json_path import (
    SQLAlchemyJSONPathExpressionBuilder,
)
from pyrsql.orms.sqlalchemy.resolver import SQLAlchemyPathResolver
from pyrsql.orms.sqlalchemy.type_inference import (
    infer_sql_function_python_type,
    is_string_python_type,
)
from pyrsql.selector.ast import (
    FieldSelector,
    FunctionSelector,
    LiteralSelector,
)
from pyrsql.sorting.ast import SortDirection

if TYPE_CHECKING:
    from sqlalchemy.sql.elements import ColumnElement

    from pyrsql.core.options import SortOptions
    from pyrsql.orms.sqlalchemy.types import (
        SQLAlchemyJoinPlan,
        SQLAlchemyResolvedPath,
    )
    from pyrsql.selector.ast import SelectorNode
    from pyrsql.sorting.ast import SortField


_JSON_SORT_PYTHON_TYPES = MappingProxyType(
    {
        JSONSortScalarType.TEXT: str,
        JSONSortScalarType.INTEGER: int,
        JSONSortScalarType.FLOAT: float,
        JSONSortScalarType.NUMERIC: float,
        JSONSortScalarType.BOOLEAN: bool,
    },
)


class SQLAlchemySortTranslator:
    """Lowers semantically validated sort fields to SQLAlchemy order clauses."""

    __slots__ = ("_json_path_builder", "_path_resolver")

    def __init__(
        self,
        *,
        path_resolver: SQLAlchemyPathResolver | None = None,
        json_path_builder: SQLAlchemyJSONPathExpressionBuilder | None = None,
    ) -> None:
        """Initializes the translator with reusable helper collaborators."""
        self._path_resolver = (
            SQLAlchemyPathResolver()
            if path_resolver is None
            else path_resolver
        )
        self._json_path_builder = (
            SQLAlchemyJSONPathExpressionBuilder()
            if json_path_builder is None
            else json_path_builder
        )

    def translate(
        self,
        model: type[Any],
        sort_fields: tuple[SortField, ...],
        *,
        options: SortOptions | None = None,
    ) -> tuple[
        tuple[SQLAlchemyJoinPlan, ...],
        tuple[ColumnElement[Any], ...],
    ]:
        """Lowers bound sort IR for a mapped model.

        Returns:
            Join plans and ORDER BY clauses.
        """
        joins: list[SQLAlchemyJoinPlan] = []
        order_clauses: list[ColumnElement[Any]] = []
        for field in sort_fields:
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
                ),
            )
        return tuple(joins), tuple(order_clauses)

    def _translate_selector(
        self,
        model: type[Any],
        selector: SelectorNode,
        *,
        options: SortOptions | None = None,
    ) -> tuple[
        tuple[SQLAlchemyJoinPlan, ...],
        ColumnElement[Any],
        type[Any] | None,
    ]:
        """Lowers one bound selector recursively.

        Returns:
            Join plans, an SQL expression, and an inferred Python type.

        Raises:
            TypeError: If the selector is not a supported selector node.
        """
        if isinstance(selector, FieldSelector):
            resolved_path = self._path_resolver.resolve(
                model,
                selector.raw_path,
                field_policy=options.field_policy if options else None,
            )
            return (
                resolved_path.joins,
                self._resolve_column_expression(
                    resolved_path,
                    options=options,
                ),
                (
                    self._resolve_json_python_type(
                        resolved_path.field_path,
                        options=options,
                    )
                    if resolved_path.is_json
                    else resolved_path.python_type
                ),
            )
        if isinstance(selector, LiteralSelector):
            python_type = (
                type(selector.value) if selector.value is not None else None
            )
            return (), sa.literal(selector.value), python_type

        if not isinstance(selector, FunctionSelector):
            raise TypeError("Expected FunctionSelector")
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
        function_expression = cast(
            "ColumnElement[Any]",
            function_expression,
        )
        python_type = infer_sql_function_python_type(
            selector.function_name,
            tuple(argument_types),
            function_expression=function_expression,
        )
        return (
            tuple(joins),
            function_expression,
            python_type,
        )

    def _resolve_column_expression(
        self,
        resolved_path: SQLAlchemyResolvedPath,
        *,
        options: SortOptions | None,
    ) -> ColumnElement[Any]:
        """Builds the effective SQL expression for a resolved path.

        Returns:
            The effective SQL expression for the resolved path.
        """
        base_expression = resolved_path.leaf_attribute
        if not resolved_path.is_json:
            return base_expression
        return self._json_path_builder.build_sort_expression(
            base_expression,
            resolved_path.json_path,
            field_path=resolved_path.field_path,
            options=options.json_options if options else DEFAULT_JSON_OPTIONS,
        )

    @staticmethod
    def _resolve_json_python_type(
        field_path: str,
        *,
        options: SortOptions | None,
    ) -> type[Any] | None:
        """Resolves the effective Python type for one JSON sort expression.

        Returns:
            The inferred Python type, or ``None`` when unknown.
        """
        json_options = options.json_options if options else DEFAULT_JSON_OPTIONS
        sort_type = json_options.sort_field_types.get(
            field_path,
            JSONSortScalarType.TEXT,
        )
        return _JSON_SORT_PYTHON_TYPES.get(sort_type)

    @staticmethod
    def _build_order_clause(
        expression: ColumnElement[Any],
        python_type: type[Any] | None,
        field: SortField,
    ) -> ColumnElement[Any]:
        """Builds an ORDER BY clause for a resolved sort field.

        Returns:
            A SQLAlchemy ordering expression.
        """
        if field.ignore_case and is_string_python_type(python_type):
            expression = cast("ColumnElement[Any]", sa.func.lower(expression))
        if field.direction is SortDirection.DESCENDING:
            return cast("ColumnElement[Any]", expression.desc())
        return cast("ColumnElement[Any]", expression.asc())
