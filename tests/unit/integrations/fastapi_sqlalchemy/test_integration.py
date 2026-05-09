"""Unit tests for the FastAPI + SQLAlchemy integration helper."""

from __future__ import annotations

from typing import Any, cast

import pytest
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.orm import DeclarativeBase

from pyrsql.adapters.fastapi import FastAPICriteriaConfig, RequestCriteria
from pyrsql.core.page import PageRequest
from pyrsql.core.query import Query
from pyrsql.core.sort import Sort
from pyrsql.integrations.fastapi import (
    FastAPISQLAlchemyIntegration,
    SQLAlchemyPaginatedSelect,
)
from pyrsql.orms.sqlalchemy import SQLAlchemyORM

pytest.importorskip("fastapi")

pytestmark = [pytest.mark.unit, pytest.mark.fastapi, pytest.mark.sqlalchemy]


class Base(DeclarativeBase):
    """Base model for integration helper unit tests."""


class User(Base):
    """Mapped test model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


def test_integration_exposes_configured_criteria_dependency() -> None:
    """Returns a FastAPI criteria dependency using the stored config."""
    integration = FastAPISQLAlchemyIntegration(
        criteria_config=FastAPICriteriaConfig(default_page_size=20)
    )

    dependency = integration.criteria_dependency()

    assert dependency.config.default_page_size == 20


def test_integration_rejects_invalid_public_configuration() -> None:
    """Rejects invalid ORM and criteria config objects."""
    with pytest.raises(TypeError):
        FastAPISQLAlchemyIntegration(orm="invalid")  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        FastAPISQLAlchemyIntegration(
            criteria_config="invalid"  # type: ignore[arg-type]
        )


def test_integration_reuses_cached_dependencies() -> None:
    """Reuses dependency objects for the same model and integration."""
    integration = FastAPISQLAlchemyIntegration()

    assert (
        integration.criteria_dependency() is integration.criteria_dependency()
    )
    assert integration.select_dependency(User) is integration.select_dependency(
        User
    )
    assert integration.count_select_dependency(
        User
    ) is integration.count_select_dependency(User)
    assert integration.paginated_select_dependency(
        User
    ) is integration.paginated_select_dependency(User)


def test_integration_applies_request_criteria_to_existing_select() -> None:
    """Applies query, sort, and page criteria through SQLAlchemyORM."""
    integration = FastAPISQLAlchemyIntegration(orm=SQLAlchemyORM())
    criteria = RequestCriteria(
        query=Query.parse("name==demo"),
        sort=Sort.parse("name,desc"),
        page_request=PageRequest.of(1, 10),
    )

    statement = integration.apply(select(User), User, criteria)
    compiled = str(statement.compile(compile_kwargs={"literal_binds": True}))

    assert "WHERE users.name = 'demo'" in compiled
    assert "ORDER BY users.name DESC" in compiled
    assert " LIMIT 10" in compiled
    assert " OFFSET 10" in compiled


def test_integration_builds_select_from_model() -> None:
    """Builds a select(model) and applies request criteria."""
    integration = FastAPISQLAlchemyIntegration(orm=SQLAlchemyORM())
    criteria = RequestCriteria(query=Query.parse("name==demo"))

    statement = integration.select(User, criteria)
    compiled = str(statement.compile(compile_kwargs={"literal_binds": True}))

    assert "FROM users" in compiled
    assert "WHERE users.name = 'demo'" in compiled


def test_integration_builds_count_select_ignoring_sort_and_page() -> None:
    """Builds a count statement from filtering semantics only."""
    integration = FastAPISQLAlchemyIntegration(orm=SQLAlchemyORM())
    criteria = RequestCriteria(
        query=Query.parse("name==demo"),
        sort=Sort.parse("name,desc"),
        page_request=PageRequest.of(1, 10),
    )

    statement = integration.count_select(User, criteria)
    compiled = str(statement.compile(compile_kwargs={"literal_binds": True}))

    assert "count(" in compiled.lower()
    assert "WHERE users.name = 'demo'" in compiled
    assert "ORDER BY" not in compiled
    assert " LIMIT " not in compiled
    assert " OFFSET " not in compiled


def test_integration_builds_paginated_select_bundle() -> None:
    """Builds both list and count statements for pagination workflows."""
    integration = FastAPISQLAlchemyIntegration(orm=SQLAlchemyORM())
    criteria = RequestCriteria(
        query=Query.parse("name==demo"),
        sort=Sort.parse("name,desc"),
        page_request=PageRequest.of(1, 10),
    )

    bundle = integration.paginated_select(User, criteria)

    assert isinstance(bundle, SQLAlchemyPaginatedSelect)
    statement_sql = str(
        bundle.statement.compile(compile_kwargs={"literal_binds": True})
    )
    count_sql = str(
        bundle.count_statement.compile(compile_kwargs={"literal_binds": True})
    )
    assert "ORDER BY users.name DESC" in statement_sql
    assert " LIMIT 10" in statement_sql
    assert "count(" in count_sql.lower()
    assert "ORDER BY" not in count_sql


def test_integration_rejects_invalid_request_criteria() -> None:
    """Rejects non-RequestCriteria values at public entrypoints."""
    integration = FastAPISQLAlchemyIntegration(orm=SQLAlchemyORM())

    with pytest.raises(TypeError):
        integration.select(User, "invalid")  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        integration.count_select(User, "invalid")  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        integration.paginated_select(User, "invalid")  # type: ignore[arg-type]


def test_paginated_select_rejects_invalid_statements() -> None:
    """Rejects non-select statement payloads in the paginated bundle."""
    with pytest.raises(TypeError):
        SQLAlchemyPaginatedSelect(
            statement=cast(Any, "invalid"),
            count_statement=select(User),
        )
