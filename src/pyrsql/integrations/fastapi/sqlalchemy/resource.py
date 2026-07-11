"""Declarative resource objects for FastAPI + SQLAlchemy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Depends

from pyrsql.adapters.fastapi import (
    CriteriaDependency,
    FastAPICriteriaConfig,
    RequestCriteria,
)
from pyrsql.integrations.fastapi.sqlalchemy.helpers import (
    apply_query_with_orm,
    apply_sort_and_page_with_orm,
    build_paginated_select,
    count_from_filtered_select,
    query_backend_http_errors,
    sort_backend_http_errors,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyrsql.core.sort import Sort as PyrsqlSort
    from pyrsql.integrations.fastapi.sqlalchemy.integration import (
        FastAPISQLAlchemyIntegration,
    )
    from pyrsql.integrations.fastapi.sqlalchemy.payloads import (
        SQLAlchemyPaginatedSelect,
    )
    from pyrsql.orms.sqlalchemy.types import SQLAlchemyModel, SQLAlchemySelect


class FastAPISQLAlchemyResource:
    """Declarative FastAPI + SQLAlchemy resource integration."""

    integration: FastAPISQLAlchemyIntegration
    model: SQLAlchemyModel
    criteria_config: FastAPICriteriaConfig
    _criteria_dependency: Callable[..., RequestCriteria]
    _statement_factory: Callable[[], SQLAlchemySelect] | None
    __slots__ = (
        "_criteria_dependency",
        "_statement_factory",
        "criteria_config",
        "integration",
        "model",
    )

    def __init__(
        self,
        *,
        integration: FastAPISQLAlchemyIntegration,
        model: SQLAlchemyModel,
        criteria_config: FastAPICriteriaConfig,
        default_sort: PyrsqlSort | None = None,
        statement_factory: Callable[[], SQLAlchemySelect] | None = None,
    ) -> None:
        """Creates a route-ready resource for one SQLAlchemy model."""
        self.integration = integration
        self.model = model
        self.criteria_config = criteria_config
        self._statement_factory = statement_factory
        base_dependency: Callable[..., RequestCriteria] = CriteriaDependency(
            criteria_config,
        )
        if default_sort is None:
            self._criteria_dependency = base_dependency
            return

        def dependency(
            criteria: RequestCriteria = Depends(base_dependency),
        ) -> RequestCriteria:
            if criteria.sort is not None:
                return criteria
            return RequestCriteria(
                query=criteria.query,
                sort=default_sort,
                page_request=criteria.page_request,
            )

        self._criteria_dependency = dependency

    def criteria_dependency(self) -> Callable[..., RequestCriteria]:
        """Returns route-ready request criteria for this resource.

        Returns:
            A FastAPI-compatible request criteria dependency.
        """
        return self._criteria_dependency

    def _base_statement(self) -> SQLAlchemySelect:
        """Builds the base statement for this resource.

        Returns:
            The base SQLAlchemy select statement for the resource.
        """
        if self._statement_factory is None:
            return self.integration.base_select(self.model)
        return self._statement_factory()

    def select(self, criteria: RequestCriteria) -> SQLAlchemySelect:
        """Builds a filtered select for the configured resource model.

        Returns:
            A filtered SQLAlchemy select statement.
        """
        return self.integration.apply(
            self._base_statement(),
            self.model,
            criteria,
        )

    def applier(
        self,
        criteria: RequestCriteria,
    ) -> Callable[[SQLAlchemySelect], SQLAlchemySelect]:
        """Builds a callable that applies criteria to an existing select.

        Returns:
            A callable that applies the resource's criteria to a select.
        """

        def apply_to(statement: SQLAlchemySelect) -> SQLAlchemySelect:
            return self.integration.apply(
                statement,
                self.model,
                criteria,
            )

        return apply_to

    def _filtered_statement(
        self,
        criteria: RequestCriteria,
    ) -> SQLAlchemySelect:
        """Builds the filtered base statement for validated criteria.

        Returns:
            The filtered base statement.
        """
        return apply_query_with_orm(
            self._base_statement(),
            self.model,
            criteria,
            self.integration.orm,
        )

    def _sorted_statement(
        self,
        filtered_statement: SQLAlchemySelect,
        criteria: RequestCriteria,
    ) -> SQLAlchemySelect:
        """Applies sort and page semantics to a filtered statement.

        Returns:
            The filtered statement with sort and page semantics applied.
        """
        return apply_sort_and_page_with_orm(
            filtered_statement,
            self.model,
            criteria,
            self.integration.orm,
        )

    def _paginated_bundle(
        self,
        filtered_statement: SQLAlchemySelect,
        criteria: RequestCriteria,
    ) -> SQLAlchemyPaginatedSelect:
        """Builds the list/count bundle from one filtered statement.

        Returns:
            The paired list and count statements.
        """
        return build_paginated_select(
            statement=self._sorted_statement(
                filtered_statement,
                criteria,
            ),
            filtered_statement=filtered_statement,
        )

    def count_select(self, criteria: RequestCriteria) -> SQLAlchemySelect:
        """Builds a count select for the configured resource model.

        Returns:
            A count SQLAlchemy select statement.
        """
        filtered_statement = self._filtered_statement(criteria)
        return count_from_filtered_select(filtered_statement)

    def paginated_select(
        self,
        criteria: RequestCriteria,
    ) -> SQLAlchemyPaginatedSelect:
        """Builds list and count statements for the configured model.

        Returns:
            Paired list and count SQLAlchemy statements.
        """
        filtered_statement = self._filtered_statement(criteria)
        return self._paginated_bundle(filtered_statement, criteria)

    def select_dependency(self) -> Callable[..., SQLAlchemySelect]:
        """Returns a FastAPI dependency yielding a filtered select.

        Returns:
            A FastAPI dependency that yields a filtered select statement.
        """
        criteria_dependency = self.criteria_dependency()

        def dependency(
            criteria: RequestCriteria = Depends(criteria_dependency),
        ) -> SQLAlchemySelect:
            with query_backend_http_errors(self.criteria_config):
                filtered_statement = self._filtered_statement(
                    criteria,
                )
            with sort_backend_http_errors(self.criteria_config):
                return self._sorted_statement(
                    filtered_statement,
                    criteria,
                )

        return dependency

    def applier_dependency(
        self,
    ) -> Callable[..., Callable[[SQLAlchemySelect], SQLAlchemySelect]]:
        """Returns a FastAPI dependency yielding a select applier.

        Returns:
            A FastAPI dependency that yields a select applier callable.
        """
        criteria_dependency = self.criteria_dependency()

        def dependency(
            criteria: RequestCriteria = Depends(criteria_dependency),
        ) -> Callable[[SQLAlchemySelect], SQLAlchemySelect]:
            return self.applier(criteria)

        return dependency

    def count_select_dependency(self) -> Callable[..., SQLAlchemySelect]:
        """Returns a FastAPI dependency yielding a count select.

        Returns:
            A FastAPI dependency that yields a count select statement.
        """
        criteria_dependency = self.criteria_dependency()

        def dependency(
            criteria: RequestCriteria = Depends(criteria_dependency),
        ) -> SQLAlchemySelect:
            with query_backend_http_errors(self.criteria_config):
                filtered_statement = self._filtered_statement(
                    criteria,
                )
            return count_from_filtered_select(filtered_statement)

        return dependency

    def paginated_select_dependency(
        self,
    ) -> Callable[..., SQLAlchemyPaginatedSelect]:
        """Returns a FastAPI dependency yielding list and count selects.

        Returns:
            A FastAPI dependency that yields paginated SQLAlchemy statements.
        """
        criteria_dependency = self.criteria_dependency()

        def dependency(
            criteria: RequestCriteria = Depends(criteria_dependency),
        ) -> SQLAlchemyPaginatedSelect:
            with query_backend_http_errors(self.criteria_config):
                filtered_statement = self._filtered_statement(
                    criteria,
                )
            with sort_backend_http_errors(self.criteria_config):
                return self._paginated_bundle(
                    filtered_statement,
                    criteria,
                )

        return dependency
