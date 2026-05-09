"""FastAPI + SQLAlchemy integration helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

import msgspec

try:
    from fastapi import Depends
except ImportError as error:  # pragma: no cover - import guard
    raise ImportError(
        "FastAPI integration requires installing the 'fastapi' extra: "
        "pip install pyrsql[fastapi]"
    ) from error

from sqlalchemy import func, select

from pyrsql.adapters.fastapi import (
    CriteriaDependency,
    FastAPICriteriaConfig,
    RequestCriteria,
)
from pyrsql.orms.sqlalchemy import SQLAlchemyORM
from pyrsql.orms.sqlalchemy.statement import require_sqlalchemy_select
from pyrsql.orms.sqlalchemy.types import SQLAlchemyModel, SQLAlchemySelect

_DEFAULT_SQLALCHEMY_ORM = SQLAlchemyORM()
_DEFAULT_FASTAPI_CRITERIA_CONFIG = FastAPICriteriaConfig()


class SQLAlchemyPaginatedSelect(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
):
    """Carries the list and count statements for a paginated query flow."""

    statement: SQLAlchemySelect
    count_statement: SQLAlchemySelect

    def __post_init__(self) -> None:
        """Validates the carried SQLAlchemy statements."""
        require_sqlalchemy_select(self.statement)
        require_sqlalchemy_select(self.count_statement)


class FastAPISQLAlchemyIntegration:
    """Composes the FastAPI adapter with the SQLAlchemy ORM integration."""

    __slots__ = (
        "orm",
        "criteria_config",
        "_criteria_dependency",
        "_select_dependencies",
        "_count_select_dependencies",
        "_paginated_select_dependencies",
        "_base_selects",
    )

    def __init__(
        self,
        *,
        orm: SQLAlchemyORM | None = None,
        criteria_config: FastAPICriteriaConfig | None = None,
    ) -> None:
        """Creates an integration helper for FastAPI and SQLAlchemy."""
        if orm is not None and not isinstance(orm, SQLAlchemyORM):
            raise TypeError("orm must be a SQLAlchemyORM or None.")
        if (
            criteria_config is not None
            and not isinstance(criteria_config, FastAPICriteriaConfig)
        ):
            raise TypeError(
                "criteria_config must be a FastAPICriteriaConfig or None."
            )
        self.orm = orm or _DEFAULT_SQLALCHEMY_ORM
        self.criteria_config = (
            criteria_config or _DEFAULT_FASTAPI_CRITERIA_CONFIG
        )
        self._criteria_dependency = CriteriaDependency(self.criteria_config)
        self._select_dependencies: dict[
            SQLAlchemyModel, Callable[..., SQLAlchemySelect]
        ] = {}
        self._count_select_dependencies: dict[
            SQLAlchemyModel, Callable[..., SQLAlchemySelect]
        ] = {}
        self._paginated_select_dependencies: dict[
            SQLAlchemyModel, Callable[..., SQLAlchemyPaginatedSelect]
        ] = {}
        self._base_selects: dict[SQLAlchemyModel, SQLAlchemySelect] = {}

    def criteria_dependency(self) -> CriteriaDependency:
        """Returns a configured FastAPI dependency for request criteria."""
        return self._criteria_dependency

    @staticmethod
    def _require_request_criteria(criteria: RequestCriteria) -> RequestCriteria:
        """Validates and returns request criteria objects."""
        if not isinstance(criteria, RequestCriteria):
            raise TypeError("criteria must be a RequestCriteria.")
        return criteria

    def _apply_query(
        self,
        statement: SQLAlchemySelect,
        model: SQLAlchemyModel,
        criteria: RequestCriteria,
    ) -> SQLAlchemySelect:
        """Applies only the filtering part of request criteria."""
        if criteria.query is None:
            return statement
        return cast(
            SQLAlchemySelect,
            criteria.query.apply(statement, model, orm=self.orm),
        )

    def _apply_sort_and_page(
        self,
        statement: SQLAlchemySelect,
        model: SQLAlchemyModel,
        criteria: RequestCriteria,
    ) -> SQLAlchemySelect:
        """Applies sort and page semantics on top of a filtered statement."""
        updated_statement = statement
        if criteria.sort is not None:
            updated_statement = cast(
                SQLAlchemySelect,
                criteria.sort.apply(updated_statement, model, orm=self.orm),
            )
        if criteria.page_request is not None:
            updated_statement = cast(
                SQLAlchemySelect,
                criteria.page_request.apply(
                    updated_statement,
                    model,
                    orm=self.orm,
                ),
            )
        return updated_statement

    def _filtered_select(
        self,
        model: SQLAlchemyModel,
        criteria: RequestCriteria,
    ) -> SQLAlchemySelect:
        """Builds the common filtered select used by list and count flows."""
        return self._apply_query(self._base_select(model), model, criteria)

    def _base_select(self, model: SQLAlchemyModel) -> SQLAlchemySelect:
        """Returns a cached base select(model) statement."""
        statement = self._base_selects.get(model)
        if statement is not None:
            return statement
        statement = select(model)
        self._base_selects[model] = statement
        return statement

    def _count_from_filtered_select(
        self,
        filtered_statement: SQLAlchemySelect,
    ) -> SQLAlchemySelect:
        """Builds a count statement from an already-filtered select."""
        return select(func.count()).select_from(  # pylint: disable=not-callable
            filtered_statement.order_by(None).subquery()
        )

    def apply(
        self,
        statement: SQLAlchemySelect,
        model: SQLAlchemyModel,
        criteria: RequestCriteria,
    ) -> SQLAlchemySelect:
        """Applies request criteria to an existing SQLAlchemy select."""
        require_sqlalchemy_select(statement)
        criteria = self._require_request_criteria(criteria)
        return cast(
            SQLAlchemySelect,
            criteria.apply(statement, model, orm=self.orm),
        )

    def select(
        self,
        model: SQLAlchemyModel,
        criteria: RequestCriteria,
    ) -> SQLAlchemySelect:
        """Builds a select statement for a model and applies criteria."""
        criteria = self._require_request_criteria(criteria)
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
        """Builds a count statement from the filtered query semantics only."""
        criteria = self._require_request_criteria(criteria)
        return self._count_from_filtered_select(
            self._filtered_select(model, criteria)
        )

    def paginated_select(
        self,
        model: SQLAlchemyModel,
        criteria: RequestCriteria,
    ) -> SQLAlchemyPaginatedSelect:
        """Builds both list and count statements for a paginated flow."""
        criteria = self._require_request_criteria(criteria)
        filtered_statement = self._filtered_select(model, criteria)
        return SQLAlchemyPaginatedSelect(
            statement=self._apply_sort_and_page(
                filtered_statement,
                model,
                criteria,
            ),
            count_statement=self._count_from_filtered_select(
                filtered_statement
            ),
        )

    def select_dependency(
        self,
        model: SQLAlchemyModel,
    ) -> Callable[..., SQLAlchemySelect]:
        """Returns a FastAPI dependency that yields a filtered select."""
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
        """Returns a FastAPI dependency that yields a count select."""
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
        """Returns a FastAPI dependency yielding list and count statements."""
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
