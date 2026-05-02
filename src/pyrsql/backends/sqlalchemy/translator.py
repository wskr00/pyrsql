"""Semantic expression translation for SQLAlchemy."""

from types import MappingProxyType
from typing import Any
from typing import Mapping
from typing import cast

import sqlalchemy as sa
from sqlalchemy.sql.elements import ColumnElement

from pyrsql.backends.sqlalchemy.coercion import SQLAlchemyValueCoercer
from pyrsql.backends.sqlalchemy.custom import SQLAlchemyCustomPredicate
from pyrsql.backends.sqlalchemy.custom import SQLAlchemyCustomPredicateInput
from pyrsql.backends.sqlalchemy.errors import SQLAlchemyBackendError
from pyrsql.backends.sqlalchemy.json_path import (
    SQLAlchemyJSONPathExpressionBuilder,
)
from pyrsql.backends.sqlalchemy.resolver import SQLAlchemyPathResolver
from pyrsql.backends.sqlalchemy.types import SQLAlchemyJoinPlan
from pyrsql.core.json.query import JSONPathComparison
from pyrsql.core.options import QueryOptions
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
from pyrsql.selector.semantic import SemanticColumnSelector
from pyrsql.selector.semantic import SemanticFunctionSelector
from pyrsql.selector.semantic import SemanticLiteralSelector
from pyrsql.selector.semantic import SemanticSelector
from pyrsql.semantic.ast import SemanticComparison
from pyrsql.semantic.ast import SemanticExpression
from pyrsql.semantic.ast import SemanticLogical


class SQLAlchemyExpressionTranslator:
    """Translates semantic expressions to SQLAlchemy predicates."""

    def __init__(
        self,
        *,
        path_resolver: SQLAlchemyPathResolver | None = None,
        value_coercer: SQLAlchemyValueCoercer | None = None,
        custom_predicates: (
            Mapping[str, SQLAlchemyCustomPredicate] | None
        ) = None,
        json_path_builder: (
            SQLAlchemyJSONPathExpressionBuilder | None
        ) = None,
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
        expression: SemanticExpression,
        *,
        options: QueryOptions,
        ) -> tuple[tuple[SQLAlchemyJoinPlan, ...], ColumnElement[bool]]:
        """Translates a semantic expression for a mapped model."""
        if isinstance(expression, SemanticComparison):
            return self._translate_comparison(
                model,
                expression,
                options=options,
            )
        return self._translate_logical(model, expression, options=options)

    def _translate_logical(
        self,
        model: type[Any],
        expression: SemanticLogical,
        *,
        options: QueryOptions,
    ) -> tuple[tuple[SQLAlchemyJoinPlan, ...], ColumnElement[bool]]:
        """Translates a logical semantic expression."""
        joins: list[Any] = []
        predicates: list[ColumnElement[bool]] = []
        for child in expression.children:
            child_joins, child_predicate = self.translate(
                model,
                child,
                options=options,
            )
            joins.extend(child_joins)
            predicates.append(child_predicate)
        if expression.operator.name == "AND":
            return tuple(joins), sa.and_(*predicates)
        return tuple(joins), sa.or_(*predicates)

    def _translate_comparison(
        self,
        model: type[Any],
        expression: SemanticComparison,
        *,
        options: QueryOptions,
    ) -> tuple[tuple[SQLAlchemyJoinPlan, ...], ColumnElement[bool]]:
        """Translates a comparison semantic expression."""
        field_model = None
        field_name = None
        field_path = None
        if isinstance(expression.selector, SemanticColumnSelector):
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
        selector: SemanticSelector,
        *,
        options: QueryOptions,
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
                field_policy=options.field_policy,
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

        assert isinstance(selector, SemanticFunctionSelector)
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
        raise SQLAlchemyBackendError(
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
        if self._is_string_type(python_type):
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

    def _is_string_type(self, python_type: type[Any] | None) -> bool:
        """Returns whether the resolved Python type is string-compatible."""
        if python_type is None:
            return False
        return issubclass(python_type, str)

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
