"""High-level FastAPI + SQLAlchemy integration helpers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import cast

from fastapi import Depends
from sqlalchemy import select

from pyrsql.adapters.fastapi import (
    CriteriaDependency,
    FastAPICriteriaConfig,
    RequestCriteria,
)
from pyrsql.core.sort import Sort as PyrsqlSort
from pyrsql.orms.sqlalchemy import SQLAlchemyORM
from pyrsql.orms.sqlalchemy.statement import require_sqlalchemy_select
from pyrsql.orms.sqlalchemy.types import SQLAlchemyModel, SQLAlchemySelect

from .examples import (
    build_filter_examples,
    build_sort_examples,
    merge_openapi_examples,
    normalize_default_sort,
)
from .helpers import (
    apply_query_with_orm,
    apply_sort_and_page_with_orm,
    count_from_filtered_select,
    require_request_criteria,
)
from .payloads import SQLAlchemyPaginatedSelect
from .resource import FastAPISQLAlchemyResource

_DEFAULT_SQLALCHEMY_ORM = SQLAlchemyORM()
_DEFAULT_FASTAPI_CRITERIA_CONFIG = FastAPICriteriaConfig()
_EMPTY_OPENAPI_EXAMPLES: dict[str, dict[str, object]] = {}


class FastAPISQLAlchemyIntegration:
    """Composes the FastAPI adapter with the SQLAlchemy ORM integration."""

    __slots__ = (
        "_base_selects",
        "_count_select_dependencies",
        "_criteria_dependency",
        "_paginated_select_dependencies",
        "_select_dependencies",
        "criteria_config",
        "orm",
    )

    def __init__(
        self,
        *,
        orm: SQLAlchemyORM | None = None,
        criteria_config: FastAPICriteriaConfig | None = None,
    ) -> None:
        """Creates an integration helper for FastAPI and SQLAlchemy.

        Raises:
            TypeError: If ``orm`` or ``criteria_config`` has the wrong runtime
                type.
        """
        if orm is not None and not isinstance(orm, SQLAlchemyORM):
            raise TypeError("orm must be a SQLAlchemyORM or None.")
        if criteria_config is not None and not isinstance(
            criteria_config, FastAPICriteriaConfig,
        ):
            raise TypeError(
                "criteria_config must be a FastAPICriteriaConfig or None.",
            )
        self.orm = orm or _DEFAULT_SQLALCHEMY_ORM
        self.criteria_config = (
            criteria_config or _DEFAULT_FASTAPI_CRITERIA_CONFIG
        )
        self._criteria_dependency = CriteriaDependency(self.criteria_config)
        self._select_dependencies: dict[
            SQLAlchemyModel, Callable[..., SQLAlchemySelect],
        ] = {}
        self._count_select_dependencies: dict[
            SQLAlchemyModel, Callable[..., SQLAlchemySelect],
        ] = {}
        self._paginated_select_dependencies: dict[
            SQLAlchemyModel, Callable[..., SQLAlchemyPaginatedSelect],
        ] = {}
        self._base_selects: dict[SQLAlchemyModel, SQLAlchemySelect] = {}

    def criteria_dependency(self) -> CriteriaDependency:
        """Returns a configured FastAPI dependency for request criteria.

        Returns:
            A configured FastAPI criteria dependency.
        """
        return self._criteria_dependency

    def _apply_query(
        self,
        statement: SQLAlchemySelect,
        model: SQLAlchemyModel,
        criteria: RequestCriteria,
    ) -> SQLAlchemySelect:
        """Applies only the filtering part of request criteria.

        Returns:
            A statement with query/filter semantics applied.
        """
        return apply_query_with_orm(
            statement,
            model,
            criteria,
            self.orm,
        )

    def _apply_sort_and_page(
        self,
        statement: SQLAlchemySelect,
        model: SQLAlchemyModel,
        criteria: RequestCriteria,
    ) -> SQLAlchemySelect:
        """Applies sort and page semantics on top of a filtered statement.

        Returns:
            A statement with sort and page semantics applied.
        """
        return apply_sort_and_page_with_orm(
            statement,
            model,
            criteria,
            self.orm,
        )

    def _filtered_select(
        self,
        model: SQLAlchemyModel,
        criteria: RequestCriteria,
    ) -> SQLAlchemySelect:
        """Builds the common filtered select used by list and count flows.

        Returns:
            The shared filtered select statement used by list and count flows.
        """
        return self._apply_query(self._base_select(model), model, criteria)

    def _base_select(self, model: SQLAlchemyModel) -> SQLAlchemySelect:
        """Returns a cached base select(model) statement.

        Returns:
            A cached base ``select(model)`` statement.
        """
        statement = self._base_selects.get(model)
        if statement is not None:
            return statement
        statement = select(model)
        self._base_selects[model] = statement
        return statement

    def base_select(self, model: SQLAlchemyModel) -> SQLAlchemySelect:
        """Returns the cached base select for a model.

        Returns:
            The cached base ``select(model)`` statement.
        """
        return self._base_select(model)

    def _count_from_filtered_select(
        self,
        filtered_statement: SQLAlchemySelect,
    ) -> SQLAlchemySelect:
        """Builds a count statement from an already-filtered select.

        Returns:
            A count statement derived from the filtered select.
        """
        return count_from_filtered_select(filtered_statement)

    def apply(
        self,
        statement: SQLAlchemySelect,
        model: SQLAlchemyModel,
        criteria: RequestCriteria,
    ) -> SQLAlchemySelect:
        """Applies request criteria to an existing SQLAlchemy select.

        Returns:
            A statement with all request criteria applied.
        """
        require_sqlalchemy_select(statement)
        criteria = require_request_criteria(criteria)
        return cast(
            "SQLAlchemySelect",
            criteria.apply(statement, model, orm=self.orm),
        )

    def select(
        self,
        model: SQLAlchemyModel,
        criteria: RequestCriteria,
    ) -> SQLAlchemySelect:
        """Builds a select statement for a model and applies criteria.

        Returns:
            A select statement with all request criteria applied.
        """
        criteria = require_request_criteria(criteria)
        filtered_statement = self._filtered_select(model, criteria)
        return self._apply_sort_and_page(
            filtered_statement,
            model,
            criteria,
        )

    def count_select(
        self,
        model: SQLAlchemyModel,
        criteria: RequestCriteria,
    ) -> SQLAlchemySelect:
        """Builds a count statement from the filtered query semantics only.

        Returns:
            A count statement derived from the filtered query semantics.
        """
        criteria = require_request_criteria(criteria)
        return self._count_from_filtered_select(
            self._filtered_select(model, criteria),
        )

    def paginated_select(
        self,
        model: SQLAlchemyModel,
        criteria: RequestCriteria,
    ) -> SQLAlchemyPaginatedSelect:
        """Builds both list and count statements for a paginated flow.

        Returns:
            The paired list and count statements for a paginated flow.
        """
        criteria = require_request_criteria(criteria)
        filtered_statement = self._filtered_select(model, criteria)
        return SQLAlchemyPaginatedSelect(
            statement=self._apply_sort_and_page(
                filtered_statement,
                model,
                criteria,
            ),
            count_statement=self._count_from_filtered_select(
                filtered_statement,
            ),
        )

    def select_dependency(
        self,
        model: SQLAlchemyModel,
    ) -> Callable[..., SQLAlchemySelect]:
        """Returns a FastAPI dependency that yields a filtered select.

        Returns:
            A FastAPI dependency that yields a filtered select statement.
        """
        cached_dependency = self._select_dependencies.get(model)
        if cached_dependency is not None:
            return cached_dependency
        criteria_dependency = self.criteria_dependency()

        def dependency(
            criteria: RequestCriteria = Depends(criteria_dependency),
        ) -> SQLAlchemySelect:
            return self.select(model, criteria)

        self._select_dependencies[model] = dependency
        return dependency

    def count_select_dependency(
        self,
        model: SQLAlchemyModel,
    ) -> Callable[..., SQLAlchemySelect]:
        """Returns a FastAPI dependency that yields a count select.

        Returns:
            A FastAPI dependency that yields a count select statement.
        """
        cached_dependency = self._count_select_dependencies.get(model)
        if cached_dependency is not None:
            return cached_dependency
        criteria_dependency = self.criteria_dependency()

        def dependency(
            criteria: RequestCriteria = Depends(criteria_dependency),
        ) -> SQLAlchemySelect:
            return self.count_select(model, criteria)

        self._count_select_dependencies[model] = dependency
        return dependency

    def paginated_select_dependency(
        self,
        model: SQLAlchemyModel,
    ) -> Callable[..., SQLAlchemyPaginatedSelect]:
        """Returns a FastAPI dependency yielding list and count statements.

        Returns:
            A FastAPI dependency that yields paired list and count statements.
        """
        cached_dependency = self._paginated_select_dependencies.get(model)
        if cached_dependency is not None:
            return cached_dependency
        criteria_dependency = self.criteria_dependency()

        def dependency(
            criteria: RequestCriteria = Depends(criteria_dependency),
        ) -> SQLAlchemyPaginatedSelect:
            return self.paginated_select(model, criteria)

        self._paginated_select_dependencies[model] = dependency
        return dependency

    def resource(
        self,
        model: SQLAlchemyModel,
        *,
        filterable_fields: set[str] | frozenset[str] | None = None,
        sortable_fields: set[str] | frozenset[str] | None = None,
        default_sort: str | None = None,
        statement_factory: Callable[[], SQLAlchemySelect] | None = None,
        max_page_size: int | None = None,
        query_parameter_name: str | None = None,
        sort_parameter_name: str | None = None,
        page_parameter_name: str | None = None,
        size_parameter_name: str | None = None,
        filter_examples: dict[str, dict[str, object]] | None = None,
        sort_examples: dict[str, dict[str, object]] | None = None,
    ) -> FastAPISQLAlchemyResource:
        """Builds a declarative route-ready resource for one model.

        Returns:
            A declarative FastAPI + SQLAlchemy resource for the model.
        """
        query_options = self.criteria_config.query_options
        sort_options = self.criteria_config.sort_options
        if filterable_fields is not None:
            query_options = replace(
                query_options,
                field_whitelist=frozenset(filterable_fields),
            )
        if sortable_fields is not None:
            sort_options = replace(
                sort_options,
                field_whitelist=frozenset(sortable_fields),
            )

        filter_openapi_examples = merge_openapi_examples(
            build_filter_examples(filterable_fields),
            filter_examples,
        )
        sort_openapi_examples = merge_openapi_examples(
            build_sort_examples(sortable_fields, default_sort),
            sort_examples,
        )

        criteria_config = FastAPICriteriaConfig(
            filter_parameter=(
                query_parameter_name or self.criteria_config.filter_parameter
            ),
            sort_parameter=(
                sort_parameter_name or self.criteria_config.sort_parameter
            ),
            page_parameter=(
                page_parameter_name or self.criteria_config.page_parameter
            ),
            size_parameter=(
                size_parameter_name or self.criteria_config.size_parameter
            ),
            default_page_size=self.criteria_config.default_page_size,
            max_page_size=max_page_size or self.criteria_config.max_page_size,
            one_based_paging=self.criteria_config.one_based_paging,
            query_options=query_options,
            sort_options=sort_options,
            filter_openapi_examples=(
                filter_openapi_examples or _EMPTY_OPENAPI_EXAMPLES
            ),
            sort_openapi_examples=(
                sort_openapi_examples or _EMPTY_OPENAPI_EXAMPLES
            ),
            page_openapi_examples=self.criteria_config.page_openapi_examples,
            size_openapi_examples=self.criteria_config.size_openapi_examples,
        )

        compiled_default_sort = None
        if default_sort is not None:
            compiled_default_sort = PyrsqlSort.parse(
                normalize_default_sort(default_sort),
                options=sort_options,
            )

        return FastAPISQLAlchemyResource(
            integration=self,
            model=model,
            criteria_config=criteria_config,
            default_sort=compiled_default_sort,
            statement_factory=statement_factory,
        )
