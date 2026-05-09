"""Declarative resource objects for FastAPI + SQLAlchemy."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast, runtime_checkable

from fastapi import Depends

from pyrsql.adapters.fastapi import (
    CriteriaDependency,
    FastAPICriteriaConfig,
    RequestCriteria,
)
from pyrsql.core.sort import Sort as PyrsqlSort
from pyrsql.orms.sqlalchemy.statement import require_sqlalchemy_select

from .helpers import (
    apply_query_with_orm,
    apply_sort_and_page_with_orm,
    count_from_filtered_select,
    require_request_criteria,
)
from .payloads import SQLAlchemyPaginatedSelect

if TYPE_CHECKING:
    from collections.abc import Callable

    from pyrsql.orms.sqlalchemy import SQLAlchemyORM
    from pyrsql.orms.sqlalchemy.types import SQLAlchemyModel, SQLAlchemySelect

    from .integration import FastAPISQLAlchemyIntegration


@runtime_checkable
class _ResourceIntegrationProtocol(Protocol):
    """Structural contract required by declarative resources."""

    orm: SQLAlchemyORM

    def apply(
        self,
        statement: SQLAlchemySelect,
        model: SQLAlchemyModel,
        criteria: RequestCriteria,
    ) -> SQLAlchemySelect: ...

    def base_select(self, model: SQLAlchemyModel) -> SQLAlchemySelect: ...


class FastAPISQLAlchemyResource:
    """Declarative FastAPI + SQLAlchemy resource integration."""

    integration: _ResourceIntegrationProtocol
    model: SQLAlchemyModel
    criteria_config: FastAPICriteriaConfig
    _criteria_dependency: Callable[..., RequestCriteria]
    _default_sort: PyrsqlSort | None
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
        "_count_select_dependency",
        "_criteria_dependency",
        "_default_sort",
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
        if not isinstance(integration, _ResourceIntegrationProtocol):
            raise TypeError(
                "integration must be a FastAPISQLAlchemyIntegration.",
            )
        validated_integration = cast(
            "_ResourceIntegrationProtocol",
            integration,
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
        self.integration = validated_integration
        self.model = model
        self.criteria_config = criteria_config
        self._default_sort = default_sort
        self._statement_factory = statement_factory
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
                sort=self._default_sort,
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

    def count_select(self, criteria: RequestCriteria) -> SQLAlchemySelect:
        """Builds a count select for the configured resource model.

        Returns:
            A count SQLAlchemy select statement.
        """
        validated_criteria = require_request_criteria(criteria)
        filtered_statement = apply_query_with_orm(
            self._base_statement(),
            self.model,
            validated_criteria,
            self.integration.orm,
        )
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
        filtered_statement = apply_query_with_orm(
            self._base_statement(),
            self.model,
            validated_criteria,
            self.integration.orm,
        )
        return SQLAlchemyPaginatedSelect(
            statement=apply_sort_and_page_with_orm(
                filtered_statement,
                self.model,
                validated_criteria,
                self.integration.orm,
            ),
            count_statement=count_from_filtered_select(filtered_statement),
        )

    def select_dependency(self) -> Callable[..., SQLAlchemySelect]:
        """Returns a FastAPI dependency yielding a filtered select.

        Returns:
            A FastAPI dependency that yields a filtered select statement.
        """
        if self._select_dependency is not None:
            return self._select_dependency
        criteria_dependency = self.criteria_dependency()

        def dependency(
            criteria: RequestCriteria = Depends(criteria_dependency),
        ) -> SQLAlchemySelect:
            return self.select(criteria)

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
        criteria_dependency = self.criteria_dependency()

        def dependency(
            criteria: RequestCriteria = Depends(criteria_dependency),
        ) -> SQLAlchemySelect:
            return self.count_select(criteria)

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
        criteria_dependency = self.criteria_dependency()

        def dependency(
            criteria: RequestCriteria = Depends(criteria_dependency),
        ) -> SQLAlchemyPaginatedSelect:
            return self.paginated_select(criteria)

        self._paginated_select_dependency = dependency
        return dependency
