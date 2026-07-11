"""High-level FastAPI + SQLAlchemy integration helpers."""

from __future__ import annotations

from threading import Lock
from typing import TYPE_CHECKING

from fastapi import Depends
import msgspec
from sqlalchemy import select

from pyrsql.adapters.fastapi import (
    CriteriaDependency,
    FastAPICriteriaConfig,
)
from pyrsql.core.sort import Sort as PyrsqlSort
from pyrsql.integrations.fastapi.sqlalchemy.examples import (
    build_filter_examples,
    build_sort_examples,
    merge_openapi_examples,
    normalize_default_sort,
)
from pyrsql.integrations.fastapi.sqlalchemy.helpers import (
    apply_query_with_orm,
    apply_sort_and_page_with_orm,
    build_paginated_select,
    count_from_filtered_select,
    query_backend_http_errors,
    sort_backend_http_errors,
)
from pyrsql.integrations.fastapi.sqlalchemy.resource import (
    FastAPISQLAlchemyResource,
)
from pyrsql.orms.sqlalchemy import SQLAlchemyORM

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyrsql.adapters.fastapi import (
        RequestCriteria,
    )
    from pyrsql.integrations.fastapi.sqlalchemy.payloads import (
        SQLAlchemyPaginatedSelect,
    )
    from pyrsql.orms.sqlalchemy.types import SQLAlchemyModel, SQLAlchemySelect

_DEFAULT_FASTAPI_CRITERIA_CONFIG = FastAPICriteriaConfig()


class FastAPISQLAlchemyIntegration:
    """Composes the FastAPI adapter with the SQLAlchemy ORM integration."""

    __slots__ = (
        "_base_selects",
        "_cache_lock",
        "_criteria_dependency",
        "criteria_config",
        "orm",
    )

    def __init__(
        self,
        *,
        orm: SQLAlchemyORM | None = None,
        criteria_config: FastAPICriteriaConfig | None = None,
    ) -> None:
        """Creates an integration helper for FastAPI and SQLAlchemy."""
        self.orm = SQLAlchemyORM() if orm is None else orm
        self.criteria_config = (
            _DEFAULT_FASTAPI_CRITERIA_CONFIG
            if criteria_config is None
            else criteria_config
        )
        self._criteria_dependency = CriteriaDependency(self.criteria_config)
        self._cache_lock = Lock()
        self._base_selects: dict[SQLAlchemyModel, SQLAlchemySelect] = {}

    def criteria_dependency(self) -> CriteriaDependency:
        """Returns a configured FastAPI dependency for request criteria.

        Returns:
            A configured FastAPI criteria dependency.
        """
        return self._criteria_dependency

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
        return apply_query_with_orm(
            self.base_select(model),
            model,
            criteria,
            self.orm,
        )

    def base_select(self, model: SQLAlchemyModel) -> SQLAlchemySelect:
        """Returns the cached base select for a model.

        Returns:
            The cached base ``select(model)`` statement.
        """
        statement = self._base_selects.get(model)
        if statement is not None:
            return statement
        with self._cache_lock:
            statement = self._base_selects.get(model)
            if statement is None:
                statement = select(model)
                self._base_selects[model] = statement
            return statement

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
        return criteria.apply(statement, model, orm=self.orm)

    def select(
        self,
        model: SQLAlchemyModel,
        criteria: RequestCriteria,
    ) -> SQLAlchemySelect:
        """Builds a select statement for a model and applies criteria.

        Returns:
            A select statement with all request criteria applied.
        """
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
        return count_from_filtered_select(
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
        filtered_statement = self._filtered_select(model, criteria)
        return build_paginated_select(
            statement=self._apply_sort_and_page(
                filtered_statement,
                model,
                criteria,
            ),
            filtered_statement=filtered_statement,
        )

    def select_dependency(
        self,
        model: SQLAlchemyModel,
    ) -> Callable[..., SQLAlchemySelect]:
        """Returns a FastAPI dependency that yields a filtered select.

        Returns:
            A FastAPI dependency that yields a filtered select statement.
        """
        criteria_dependency = self.criteria_dependency()

        def dependency(
            criteria: RequestCriteria = Depends(criteria_dependency),
        ) -> SQLAlchemySelect:
            with query_backend_http_errors(self.criteria_config):
                filtered_statement = self._filtered_select(
                    model,
                    criteria,
                )
            with sort_backend_http_errors(self.criteria_config):
                return self._apply_sort_and_page(
                    filtered_statement,
                    model,
                    criteria,
                )

        return dependency

    def count_select_dependency(
        self,
        model: SQLAlchemyModel,
    ) -> Callable[..., SQLAlchemySelect]:
        """Returns a FastAPI dependency that yields a count select.

        Returns:
            A FastAPI dependency that yields a count select statement.
        """
        criteria_dependency = self.criteria_dependency()

        def dependency(
            criteria: RequestCriteria = Depends(criteria_dependency),
        ) -> SQLAlchemySelect:
            with query_backend_http_errors(self.criteria_config):
                filtered_statement = self._filtered_select(
                    model,
                    criteria,
                )
            return count_from_filtered_select(filtered_statement)

        return dependency

    def paginated_select_dependency(
        self,
        model: SQLAlchemyModel,
    ) -> Callable[..., SQLAlchemyPaginatedSelect]:
        """Returns a FastAPI dependency yielding list and count statements.

        Returns:
            A FastAPI dependency that yields paired list and count statements.
        """
        criteria_dependency = self.criteria_dependency()

        def dependency(
            criteria: RequestCriteria = Depends(criteria_dependency),
        ) -> SQLAlchemyPaginatedSelect:
            with query_backend_http_errors(self.criteria_config):
                filtered_statement = self._filtered_select(
                    model,
                    criteria,
                )
            with sort_backend_http_errors(self.criteria_config):
                return build_paginated_select(
                    statement=self._apply_sort_and_page(
                        filtered_statement,
                        model,
                        criteria,
                    ),
                    filtered_statement=filtered_statement,
                )

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
            query_options = query_options.with_field_whitelist(
                frozenset(filterable_fields),
            )
        if sortable_fields is not None:
            sort_options = sort_options.with_field_whitelist(
                frozenset(sortable_fields),
            )

        filter_openapi_examples = merge_openapi_examples(
            build_filter_examples(
                model,
                filterable_fields,
                field_mapping=query_options.field_mapping,
                field_policy=query_options.field_policy,
            ),
            filter_examples,
        )
        sort_openapi_examples = merge_openapi_examples(
            build_sort_examples(sortable_fields, default_sort),
            sort_examples,
        )

        criteria_config = msgspec.structs.replace(
            self.criteria_config,
            filter_parameter=(
                self.criteria_config.filter_parameter
                if query_parameter_name is None
                else query_parameter_name
            ),
            sort_parameter=(
                self.criteria_config.sort_parameter
                if sort_parameter_name is None
                else sort_parameter_name
            ),
            page_parameter=(
                self.criteria_config.page_parameter
                if page_parameter_name is None
                else page_parameter_name
            ),
            size_parameter=(
                self.criteria_config.size_parameter
                if size_parameter_name is None
                else size_parameter_name
            ),
            max_page_size=(
                self.criteria_config.max_page_size
                if max_page_size is None
                else max_page_size
            ),
            query_options=query_options,
            sort_options=sort_options,
            filter_openapi_examples=filter_openapi_examples,
            sort_openapi_examples=sort_openapi_examples,
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
