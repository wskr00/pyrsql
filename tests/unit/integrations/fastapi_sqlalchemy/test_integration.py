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
    FastAPISQLAlchemyResource,
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


class OtherModel(Base):
    """Second mapped model used for compatibility validation tests."""

    __tablename__ = "other_models"

    id = Column(Integer, primary_key=True)


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

    with pytest.raises(TypeError):
        FastAPISQLAlchemyResource(
            integration=cast(Any, object()),
            model=User,
            criteria_config=FastAPICriteriaConfig(),
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


def test_integration_builds_declarative_resource() -> None:
    """Builds a route-ready declarative resource object."""
    integration = FastAPISQLAlchemyIntegration(orm=SQLAlchemyORM())

    resource = integration.resource(
        User,
        filterable_fields={"name"},
        sortable_fields={"name"},
        default_sort="name,desc",
        max_page_size=50,
        filter_examples={
            "by_name": {"summary": "By name", "value": "name==demo"}
        },
    )

    assert isinstance(resource, FastAPISQLAlchemyResource)
    assert resource.criteria_config.query_options.field_whitelist == {"name"}
    assert resource.criteria_config.sort_options.field_whitelist == {"name"}
    assert resource.criteria_config.max_page_size == 50
    assert (
        resource.criteria_config.filter_openapi_examples["by_name"]["value"]
        == "name==demo"
    )
    assert (
        resource.criteria_config.sort_openapi_examples["default_sort"][
            "value"
        ]
        == "name,desc"
    )


def test_resource_generates_automatic_examples() -> None:
    """Generates filter and sort examples from declarative config."""
    integration = FastAPISQLAlchemyIntegration(orm=SQLAlchemyORM())

    resource = integration.resource(
        User,
        filterable_fields={"id", "name"},
        sortable_fields={"name"},
        default_sort="-name",
    )

    assert (
        resource.criteria_config.filter_openapi_examples["filter_by_id"][
            "value"
        ]
        == "id==1"
    )
    assert (
        resource.criteria_config.filter_openapi_examples[
            "filter_by_name"
        ]["value"]
        == "name==demo"
    )
    assert (
        resource.criteria_config.sort_openapi_examples[
            "sort_by_name_asc"
        ]["value"]
        == "name,asc"
    )
    assert (
        resource.criteria_config.sort_openapi_examples["default_sort"][
            "value"
        ]
        == "name,desc"
    )


def test_resource_applies_default_sort_when_request_sort_is_absent() -> None:
    """Applies declarative default sort when request sort is absent."""
    integration = FastAPISQLAlchemyIntegration(orm=SQLAlchemyORM())
    resource = integration.resource(User, default_sort="-name")

    criteria_dependency = resource.criteria_dependency()
    criteria = criteria_dependency(RequestCriteria())
    statement = resource.select(criteria)
    compiled = str(statement.compile(compile_kwargs={"literal_binds": True}))

    assert "ORDER BY users.name DESC" in compiled


def test_resource_applier_transforms_existing_select() -> None:
    """Applies resource criteria to an existing base select."""
    integration = FastAPISQLAlchemyIntegration(orm=SQLAlchemyORM())
    resource = integration.resource(User, default_sort="-name")
    criteria = resource.criteria_dependency()(RequestCriteria())

    statement = resource.applier(criteria)(
        select(User).where(User.id > 10)
    )
    compiled = str(statement.compile(compile_kwargs={"literal_binds": True}))

    assert "WHERE users.id > 10" in compiled
    assert "ORDER BY users.name DESC" in compiled


def test_resource_uses_statement_factory_for_select_and_count() -> None:
    """Uses a custom base statement for list and count flows."""
    integration = FastAPISQLAlchemyIntegration(orm=SQLAlchemyORM())
    resource = integration.resource(
        User,
        statement_factory=lambda: select(User).where(User.id > 10),
        default_sort="-name",
    )
    criteria = resource.criteria_dependency()(RequestCriteria())

    statement = resource.select(criteria)
    count_statement = resource.count_select(criteria)
    statement_sql = str(
        statement.compile(compile_kwargs={"literal_binds": True})
    )
    count_sql = str(
        count_statement.compile(compile_kwargs={"literal_binds": True})
    )

    assert "WHERE users.id > 10" in statement_sql
    assert "ORDER BY users.name DESC" in statement_sql
    assert "WHERE users.id > 10" in count_sql
    assert "ORDER BY" not in count_sql


def test_resource_uses_statement_factory_for_paginated_bundle() -> None:
    """Uses a custom base statement in paginated bundle generation."""
    integration = FastAPISQLAlchemyIntegration(orm=SQLAlchemyORM())
    resource = integration.resource(
        User,
        statement_factory=lambda: select(User).where(User.id > 10),
        default_sort="-name",
    )
    criteria = resource.criteria_dependency()(
        RequestCriteria(page_request=PageRequest.of(0, 5))
    )

    bundle = resource.paginated_select(criteria)
    statement_sql = str(
        bundle.statement.compile(compile_kwargs={"literal_binds": True})
    )
    count_sql = str(
        bundle.count_statement.compile(compile_kwargs={"literal_binds": True})
    )

    assert "WHERE users.id > 10" in statement_sql
    assert " LIMIT 5" in statement_sql
    assert "WHERE users.id > 10" in count_sql
    assert "ORDER BY" not in count_sql


def test_resource_rejects_invalid_statement_factory_result() -> None:
    """Rejects statement factories that do not return SQLAlchemy Select."""
    integration = FastAPISQLAlchemyIntegration(orm=SQLAlchemyORM())
    resource = integration.resource(
        User,
        statement_factory=lambda: cast(Any, "invalid"),
    )

    with pytest.raises(TypeError):
        resource.select(RequestCriteria())


def test_resource_rejects_incompatible_statement_factory_model() -> None:
    """Rejects statement factories that target a different mapped model."""
    integration = FastAPISQLAlchemyIntegration(orm=SQLAlchemyORM())
    resource = integration.resource(
        User,
        statement_factory=lambda: select(OtherModel),
    )

    with pytest.raises(
        TypeError,
        match="statement_factory must return a Select compatible",
    ):
        resource.select(RequestCriteria())


def test_resource_reuses_integration_cached_base_select() -> None:
    """Reuses the integration cached base select on the common path."""
    integration = FastAPISQLAlchemyIntegration(orm=SQLAlchemyORM())
    resource = integration.resource(User)

    assert resource.select(RequestCriteria()) is integration.base_select(User)


def test_resource_reuses_cached_dependencies() -> None:
    """Reuses dependency objects created by a declarative resource."""
    integration = FastAPISQLAlchemyIntegration(orm=SQLAlchemyORM())
    resource = integration.resource(User, default_sort="-name")

    assert resource.applier_dependency() is resource.applier_dependency()
    assert resource.select_dependency() is resource.select_dependency()
    assert (
        resource.count_select_dependency()
        is resource.count_select_dependency()
    )
    assert (
        resource.paginated_select_dependency()
        is resource.paginated_select_dependency()
    )


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
