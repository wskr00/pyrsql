"""Bound query IR lowering for SQLAlchemy."""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.sql.elements import ColumnElement

from pyrsql.core.json.query import JSONPathComparison
from pyrsql.core.options import QueryOptions
from pyrsql.ir.query import (
    BoundComparison,
    BoundField,
    BoundFunction,
    BoundLiteral,
    BoundLogical,
    BoundSelectorNode,
)
from pyrsql.orms.sqlalchemy.coercion import SQLAlchemyValueCoercer
from pyrsql.orms.sqlalchemy.custom import (
    SQLAlchemyCustomPredicate,
    SQLAlchemyCustomPredicateInput,
)
from pyrsql.orms.sqlalchemy.errors import SQLAlchemyORMError
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
from pyrsql.parsing.ast import LogicalOperator
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


class SQLAlchemyExpressionTranslator:
    """Lowers bound query IR to SQLAlchemy predicates.

    The translator resolves ORM paths, coerces values, and produces SQLAlchemy
    join plans and predicates from bound query IR.
    """

    def __init__(
        self,
        *,
        path_resolver: SQLAlchemyPathResolver | None = None,
        value_coercer: SQLAlchemyValueCoercer | None = None,
        custom_predicates: (
            Mapping[str, SQLAlchemyCustomPredicate] | None
        ) = None,
        json_path_builder: SQLAlchemyJSONPathExpressionBuilder | None = None,
    ) -> None:
        self._path_resolver = path_resolver or SQLAlchemyPathResolver()
        self._value_coercer = value_coercer or SQLAlchemyValueCoercer()
        self._json_path_builder = (
            json_path_builder or SQLAlchemyJSONPathExpressionBuilder()
        )
        self._custom_predicates = MappingProxyType(
            dict(custom_predicates or {})
        )

    def translate(
        self,
        model: type[Any],
        expression: BoundComparison | BoundLogical,
        *,
        options: QueryOptions,
    ) -> tuple[tuple[SQLAlchemyJoinPlan, ...], ColumnElement[bool]]:
        """Lowers one bound query expression for a mapped model.

        Args:
            model: SQLAlchemy mapped class used to resolve fields.
            expression: Bound query IR to lower.
            options: Query configuration used during translation.

        Returns:
            A tuple containing join plans and the SQLAlchemy predicate.
        """
        if isinstance(expression, BoundComparison):
            return self._translate_comparison(
                model,
                expression,
                options=options,
            )
        return self._translate_logical(model, expression, options=options)

    def _translate_logical(
        self,
        model: type[Any],
        expression: BoundLogical,
        *,
        options: QueryOptions,
    ) -> tuple[tuple[SQLAlchemyJoinPlan, ...], ColumnElement[bool]]:
        """Lowers one logical bound expression."""
        joins: list[SQLAlchemyJoinPlan] = []
        predicates: list[ColumnElement[bool]] = []
        for child in expression.children:
            child_joins, child_predicate = self.translate(
                model,
                cast(BoundComparison | BoundLogical, child),
                options=options,
            )
            joins.extend(child_joins)
            predicates.append(child_predicate)
        if expression.operator is LogicalOperator.AND:
            return tuple(joins), sa.and_(*predicates)
        return tuple(joins), sa.or_(*predicates)

    def _translate_comparison(
        self,
        model: type[Any],
        expression: BoundComparison,
        *,
        options: QueryOptions,
    ) -> tuple[tuple[SQLAlchemyJoinPlan, ...], ColumnElement[bool]]:
        """Lowers one comparison bound expression."""
        field_model = None
        field_name = None
        field_path = None
        if isinstance(expression.selector, BoundField):
            resolved_path = self._path_resolver.resolve(
                model,
                expression.selector.field_path,
                field_policy=options.field_policy,
            )
            selector_joins = resolved_path.joins
            selector_expression = resolved_path.leaf_attribute
            python_type = resolved_path.python_type
            field_model = resolved_path.leaf_model
            field_name = getattr(resolved_path.leaf_attribute, "key", None)
            field_path = resolved_path.field_path
            if resolved_path.is_json:
                json_comparison = JSONPathComparison.from_raw_arguments(
                    path=resolved_path.json_path,
                    operator_name=expression.operator.name,
                    raw_arguments=tuple(
                        (argument.text, argument.quoted)
                        for argument in expression.arguments
                    ),
                )
                predicate = self._json_path_builder.build_filter_expression(
                    selector_expression,
                    json_comparison,
                    options=options.json_options,
                )
                if self._should_use_exists_predicate(
                    selector_joins,
                    options=options,
                ):
                    return (), self._wrap_exists_predicate(
                        selector_joins,
                        predicate,
                    )
                return selector_joins, predicate
        else:
            selector_joins, selector_expression, python_type = (
                self._translate_selector(
                    model,
                    expression.selector,
                    options=options,
                )
            )
        custom_predicate = options.custom_predicates.get(
            expression.operator.name
        )
        argument_type = (
            custom_predicate.argument_type
            if custom_predicate is not None
            else python_type
        )
        coerced_values = tuple(
            self._value_coercer.coerce(
                argument.text,
                argument_type,
                field_converter_set=options.field_converter_set,
                model=field_model,
                field_name=field_name,
                field_path=field_path,
                registry=options.value_converter_registry,
            )
            for argument in expression.arguments
        )
        predicate = self._build_predicate(
            selector_expression,
            python_type,
            expression.operator.name,
            coerced_values,
            options=options,
        )
        if self._should_use_exists_predicate(
            selector_joins,
            options=options,
        ):
            return (), self._wrap_exists_predicate(
                selector_joins,
                predicate,
            )
        return selector_joins, predicate

    def _translate_selector(
        self,
        model: type[Any],
        selector: BoundSelectorNode,
        *,
        options: QueryOptions,
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
                field_policy=options.field_policy,
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

    def _build_predicate(
        self,
        expression: ColumnElement[Any],
        python_type: type[Any] | None,
        operator_name: str,
        values: tuple[Any, ...],
        *,
        options: QueryOptions,
    ) -> ColumnElement[bool]:
        """Builds a SQLAlchemy predicate for a resolved path."""
        custom_predicate = self._custom_predicates.get(operator_name)
        if custom_predicate is not None:
            return custom_predicate(
                SQLAlchemyCustomPredicateInput(
                    expression=expression,
                    python_type=python_type,
                    values=values,
                    options=options,
                )
            )
        if operator_name == EQUAL.name:
            return self._build_equality_predicate(
                expression,
                python_type,
                values[0],
                negated=False,
                options=options,
            )
        if operator_name == NOT_EQUAL.name:
            return self._build_equality_predicate(
                expression,
                python_type,
                values[0],
                negated=True,
                options=options,
            )
        if operator_name == GREATER_THAN.name:
            return cast(ColumnElement[bool], expression > values[0])
        if operator_name == GREATER_THAN_OR_EQUAL.name:
            return cast(ColumnElement[bool], expression >= values[0])
        if operator_name == LESS_THAN.name:
            return cast(ColumnElement[bool], expression < values[0])
        if operator_name == LESS_THAN_OR_EQUAL.name:
            return cast(ColumnElement[bool], expression <= values[0])
        if operator_name == IN.name:
            return cast(ColumnElement[bool], expression.in_(values))
        if operator_name == NOT_IN.name:
            return cast(ColumnElement[bool], expression.not_in(values))
        if operator_name == IS_NULL.name:
            return cast(ColumnElement[bool], expression.is_(None))
        if operator_name == NOT_NULL.name:
            return cast(ColumnElement[bool], expression.is_not(None))
        if operator_name == LIKE.name:
            return self._build_contains_predicate(
                expression,
                str(values[0]),
                ignore_case=False,
                negated=False,
                options=options,
            )
        if operator_name == NOT_LIKE.name:
            return self._build_contains_predicate(
                expression,
                str(values[0]),
                ignore_case=False,
                negated=True,
                options=options,
            )
        if operator_name == IGNORE_CASE.name:
            return self._build_case_insensitive_equality_predicate(
                expression,
                str(values[0]),
                negated=False,
            )
        if operator_name == IGNORE_CASE_LIKE.name:
            return self._build_contains_predicate(
                expression,
                str(values[0]),
                ignore_case=True,
                negated=False,
                options=options,
            )
        if operator_name == IGNORE_CASE_NOT_LIKE.name:
            return self._build_contains_predicate(
                expression,
                str(values[0]),
                ignore_case=True,
                negated=True,
                options=options,
            )
        if operator_name == BETWEEN.name:
            return cast(
                ColumnElement[bool],
                expression.between(values[0], values[1]),
            )
        if operator_name == NOT_BETWEEN.name:
            return cast(
                ColumnElement[bool],
                sa.not_(expression.between(values[0], values[1])),
            )
        raise SQLAlchemyORMError(
            f"Unsupported SQLAlchemy operator {operator_name!r}."
        )

    def _build_equality_predicate(
        self,
        expression: ColumnElement[Any],
        python_type: type[Any] | None,
        value: Any,
        *,
        negated: bool,
        options: QueryOptions,
    ) -> ColumnElement[bool]:
        """Builds equality semantics, including RSQL wildcard handling."""
        predicate: ColumnElement[bool]
        if is_string_python_type(python_type):
            predicate = self._build_string_equality_predicate(
                expression,
                str(value),
                options=options,
            )
        else:
            predicate = cast(ColumnElement[bool], expression == value)
        if not negated:
            return predicate
        return cast(ColumnElement[bool], sa.not_(predicate))

    def _build_string_equality_predicate(
        self,
        expression: ColumnElement[Any],
        value: str,
        *,
        options: QueryOptions,
    ) -> ColumnElement[bool]:
        """Builds equality for string values with wildcard semantics."""
        if options.strict_equality:
            return expression == value

        ignore_case = "^" in value
        normalized_value = value.replace("^", "")
        if "*" in normalized_value:
            pattern = normalized_value.replace("*", "%")
            return self._build_pattern_predicate(
                expression,
                pattern,
                ignore_case=ignore_case,
                negated=False,
                options=options,
            )
        if ignore_case:
            return self._build_case_insensitive_equality_predicate(
                expression,
                normalized_value,
                negated=False,
            )
        return expression == normalized_value

    def _build_case_insensitive_equality_predicate(
        self,
        expression: ColumnElement[Any],
        value: str,
        *,
        negated: bool,
    ) -> ColumnElement[bool]:
        """Builds a case-insensitive equality predicate."""
        predicate = sa.func.lower(expression) == value.lower()
        if not negated:
            return predicate
        return cast(ColumnElement[bool], sa.not_(predicate))

    def _build_contains_predicate(
        self,
        expression: ColumnElement[Any],
        value: str,
        *,
        ignore_case: bool,
        negated: bool,
        options: QueryOptions,
    ) -> ColumnElement[bool]:
        """Builds contains-style LIKE semantics with optional escaping."""
        pattern = f"%{value}%"
        return self._build_pattern_predicate(
            expression,
            pattern,
            ignore_case=ignore_case,
            negated=negated,
            options=options,
        )

    def _build_pattern_predicate(
        self,
        expression: ColumnElement[Any],
        pattern: str,
        *,
        ignore_case: bool,
        negated: bool,
        options: QueryOptions,
    ) -> ColumnElement[bool]:
        """Builds a LIKE or ILIKE predicate with optional escaping."""
        escape_character = options.like_escape_character
        if ignore_case:
            if negated:
                return cast(
                    ColumnElement[bool],
                    expression.not_ilike(pattern, escape=escape_character),
                )
            return cast(
                ColumnElement[bool],
                expression.ilike(pattern, escape=escape_character),
            )
        if negated:
            return cast(
                ColumnElement[bool],
                expression.not_like(pattern, escape=escape_character),
            )
        return cast(
            ColumnElement[bool],
            expression.like(pattern, escape=escape_character),
        )

    def _should_use_exists_predicate(
        self,
        joins: tuple[SQLAlchemyJoinPlan, ...],
        *,
        options: QueryOptions,
    ) -> bool:
        """Returns whether a filter should use relationship EXISTS forms."""
        if options.join_hints:
            return False
        return any(join_plan.is_collection for join_plan in joins)

    def _wrap_exists_predicate(
        self,
        joins: tuple[SQLAlchemyJoinPlan, ...],
        predicate: ColumnElement[bool],
    ) -> ColumnElement[bool]:
        """Wraps a leaf predicate using relationship any()/has()."""
        wrapped_predicate = predicate
        for join_plan in reversed(joins):
            if join_plan.is_collection:
                wrapped_predicate = join_plan.attribute.any(wrapped_predicate)
                continue
            wrapped_predicate = join_plan.attribute.has(wrapped_predicate)
        return wrapped_predicate
