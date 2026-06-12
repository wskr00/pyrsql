"""Declarative resource objects for FastAPI + SQLAlchemy."""

from __future__ import annotations

from threading import Lock
from typing import TYPE_CHECKING

from fastapi import Depends

from pyrsql.adapters.fastapi import (
    CriteriaDependency,
    FastAPICriteriaConfig,
    RequestCriteria,
)
from pyrsql.core.sort import Sort as PyrsqlSort
from pyrsql.integrations.fastapi.sqlalchemy.helpers import (
    apply_query_with_orm,
    apply_sort_and_page_with_orm,
    count_from_filtered_select,
    query_backend_http_errors,
    require_request_criteria,
    sort_backend_http_errors,
)
import pyrsql.integrations.fastapi.sqlalchemy.integration
from pyrsql.integrations.fastapi.sqlalchemy.payloads import (
    SQLAlchemyPaginatedSelect,
)
from pyrsql.orms.sqlalchemy.statement import require_sqlalchemy_select

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyrsql.integrations.fastapi.sqlalchemy.integration import (
        FastAPISQLAlchemyIntegration,
    )
    from pyrsql.orms.sqlalchemy.types import SQLAlchemyModel, SQLAlchemySelect


class FastAPISQLAlchemyResource:
    """Declarative FastAPI + SQLAlchemy resource integration."""

    integration: FastAPISQLAlchemyIntegration
    model: SQLAlchemyModel
    criteria_config: FastAPICriteriaConfig
    _criteria_dependency: Callable[..., RequestCriteria]
    _statement_factory: Callable[[], SQLAlchemySelect] | None
    _applier_dependency: (
        Callable[..., Callable[[SQLAlchemySelect], SQLAlchemySelect]] | None
    )
    _select_dependency: Callable[..., SQLAlchemySelect] | None
    _count_select_dependency: Callable[..., SQLAlchemySelect] | None
    _paginated_select_dependency: (
        Callable[..., SQLAlchemyPaginatedSelect] | None
    )

    __slots__ = (
        "_applier_dependency",
        "_cache_lock",
        "_count_select_dependency",
        "_criteria_dependency",
        "_paginated_select_dependency",
        "_select_dependency",
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
        """Creates a route-ready resource for one SQLAlchemy model.

        Raises:
            TypeError: If the integration, criteria config, default sort, or
                statement factory have the wrong runtime type.
        """
        integration_type = (
            pyrsql.integrations.fastapi.sqlalchemy.integration.FastAPISQLAlchemyIntegration
        )
        if not isinstance(
            integration,
            integration_type,
        ):
            raise TypeError(
                "integration must be a FastAPISQLAlchemyIntegration.",
            )
        if not isinstance(criteria_config, FastAPICriteriaConfig):
            raise TypeError("criteria_config must be a FastAPICriteriaConfig.")
        if default_sort is not None and not isinstance(
            default_sort,
            PyrsqlSort,
        ):
            raise TypeError("default_sort must be a Sort or None.")
        if statement_factory is not None and not callable(statement_factory):
            raise TypeError("statement_factory must be a callable or None.")
        self.integration = integration
        self.model = model
        self.criteria_config = criteria_config
        self._statement_factory = statement_factory
        self._cache_lock = Lock()
        self._applier_dependency: (
            Callable[..., Callable[[SQLAlchemySelect], SQLAlchemySelect]] | None
        ) = None
        self._select_dependency: Callable[..., SQLAlchemySelect] | None = None
        self._count_select_dependency: (
            Callable[..., SQLAlchemySelect] | None
        ) = None
        self._paginated_select_dependency: (
            Callable[..., SQLAlchemyPaginatedSelect] | None
        ) = None
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

        Raises:
            TypeError: If the statement factory returns an incompatible
                statement.
        """
        if self._statement_factory is None:
            return self.integration.base_select(self.model)
        statement = require_sqlalchemy_select(self._statement_factory())
        if not any(
            description.get("entity") is self.model
            for description in statement.column_descriptions
        ):
            raise TypeError(
                "statement_factory must return a Select compatible "
                f"with model {self.model.__name__}.",
            )
        return statement

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
        validated_criteria = require_request_criteria(criteria)

        def apply_to(statement: SQLAlchemySelect) -> SQLAlchemySelect:
            return self.integration.apply(
                statement,
                self.model,
                validated_criteria,
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
        return SQLAlchemyPaginatedSelect(
            statement=self._sorted_statement(
                filtered_statement,
                criteria,
            ),
            count_statement=count_from_filtered_select(filtered_statement),
        )

    def count_select(self, criteria: RequestCriteria) -> SQLAlchemySelect:
        """Builds a count select for the configured resource model.

        Returns:
            A count SQLAlchemy select statement.
        """
        validated_criteria = require_request_criteria(criteria)
        filtered_statement = self._filtered_statement(validated_criteria)
        return count_from_filtered_select(filtered_statement)

    def paginated_select(
        self,
        criteria: RequestCriteria,
    ) -> SQLAlchemyPaginatedSelect:
        """Builds list and count statements for the configured model.

        Returns:
            Paired list and count SQLAlchemy statements.
        """
        validated_criteria = require_request_criteria(criteria)
        filtered_statement = self._filtered_statement(validated_criteria)
        return self._paginated_bundle(filtered_statement, validated_criteria)

    def select_dependency(self) -> Callable[..., SQLAlchemySelect]:
        """Returns a FastAPI dependency yielding a filtered select.

        Returns:
            A FastAPI dependency that yields a filtered select statement.
        """
        if self._select_dependency is not None:
            return self._select_dependency
        with self._cache_lock:
            if self._select_dependency is not None:
                return self._select_dependency
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

            self._select_dependency = dependency
            return dependency

    def applier_dependency(
        self,
    ) -> Callable[..., Callable[[SQLAlchemySelect], SQLAlchemySelect]]:
        """Returns a FastAPI dependency yielding a select applier.

        Returns:
            A FastAPI dependency that yields a select applier callable.
        """
        if self._applier_dependency is not None:
            return self._applier_dependency
        with self._cache_lock:
            if self._applier_dependency is not None:
                return self._applier_dependency
            criteria_dependency = self.criteria_dependency()

            def dependency(
                criteria: RequestCriteria = Depends(criteria_dependency),
            ) -> Callable[[SQLAlchemySelect], SQLAlchemySelect]:
                return self.applier(criteria)

            self._applier_dependency = dependency
            return dependency

    def count_select_dependency(self) -> Callable[..., SQLAlchemySelect]:
        """Returns a FastAPI dependency yielding a count select.

        Returns:
            A FastAPI dependency that yields a count select statement.
        """
        if self._count_select_dependency is not None:
            return self._count_select_dependency
        with self._cache_lock:
            if self._count_select_dependency is not None:
                return self._count_select_dependency
            criteria_dependency = self.criteria_dependency()

            def dependency(
                criteria: RequestCriteria = Depends(criteria_dependency),
            ) -> SQLAlchemySelect:
                with query_backend_http_errors(self.criteria_config):
                    filtered_statement = self._filtered_statement(
                        criteria,
                    )
                return count_from_filtered_select(filtered_statement)

            self._count_select_dependency = dependency
            return dependency

    def paginated_select_dependency(
        self,
    ) -> Callable[..., SQLAlchemyPaginatedSelect]:
        """Returns a FastAPI dependency yielding list and count selects.

        Returns:
            A FastAPI dependency that yields paginated SQLAlchemy statements.
        """
        if self._paginated_select_dependency is not None:
            return self._paginated_select_dependency
        with self._cache_lock:
            if self._paginated_select_dependency is not None:
                return self._paginated_select_dependency
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

            self._paginated_select_dependency = dependency
            return dependency
