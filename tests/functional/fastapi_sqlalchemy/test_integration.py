"""Functional tests for the FastAPI + SQLAlchemy integration helper."""

from typing import Annotated, Any

import pytest

# pylint: disable=wrong-import-position


pytest.importorskip("fastapi")
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.orm import DeclarativeBase

from pyrsql.integrations.fastapi import FastAPISQLAlchemyIntegration

pytestmark = [
    pytest.mark.functional,
    pytest.mark.fastapi,
    pytest.mark.sqlalchemy,
]


class Base(DeclarativeBase):
    """Base model for functional integration tests."""


class User(Base):
    """Mapped test model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


def test_select_dependency_returns_a_filtered_statement() -> None:
    """Builds a FastAPI dependency that yields a SQLAlchemy select."""
    app = FastAPI()
    integration = FastAPISQLAlchemyIntegration()

    @app.get("/users")
    def list_users(
        statement: Annotated[Any, Depends(integration.select_dependency(User))],
    ) -> dict[str, str]:
        return {
            "sql": str(
                statement.compile(compile_kwargs={"literal_binds": True}),
            ),
        }

    response = TestClient(app).get(
        "/users",
        params={"filter": "name==demo", "sort": "name,asc", "size": 5},
    )

    assert response.status_code == 200
    sql = response.json()["sql"]
    assert "WHERE users.name = 'demo'" in sql
    assert "ORDER BY users.name ASC" in sql
    assert " LIMIT 5" in sql


def test_count_select_dependency_returns_a_count_statement() -> None:
    """Builds a FastAPI dependency that yields a count select."""
    app = FastAPI()
    integration = FastAPISQLAlchemyIntegration()

    @app.get("/users/count")
    def count_users(
        statement: Annotated[
            Any, Depends(integration.count_select_dependency(User))
        ],
    ) -> dict[str, str]:
        return {
            "sql": str(
                statement.compile(compile_kwargs={"literal_binds": True}),
            ),
        }

    response = TestClient(app).get(
        "/users/count",
        params={"filter": "name==demo", "sort": "name,asc", "size": 5},
    )

    assert response.status_code == 200
    sql = response.json()["sql"]
    assert "count(" in sql.lower()
    assert "WHERE users.name = 'demo'" in sql
    assert "ORDER BY" not in sql
    assert " LIMIT " not in sql


def test_paginated_select_dependency_returns_both_statements() -> None:
    """Builds a FastAPI dependency that yields list and count statements."""
    app = FastAPI()
    integration = FastAPISQLAlchemyIntegration()

    @app.get("/users/paginated")
    def paginated_users(
        bundle: Annotated[
            Any, Depends(integration.paginated_select_dependency(User))
        ],
    ) -> dict[str, str]:
        return {
            "statement": str(
                bundle.statement.compile(
                    compile_kwargs={"literal_binds": True}
                ),
            ),
            "count_statement": str(
                bundle.count_statement.compile(
                    compile_kwargs={"literal_binds": True},
                ),
            ),
        }

    response = TestClient(app).get(
        "/users/paginated",
        params={"filter": "name==demo", "sort": "name,asc", "size": 5},
    )

    assert response.status_code == 200
    statement_sql = response.json()["statement"]
    count_sql = response.json()["count_statement"]
    assert "ORDER BY users.name ASC" in statement_sql
    assert " LIMIT 5" in statement_sql
    assert "count(" in count_sql.lower()
    assert "ORDER BY" not in count_sql


def test_resource_dependency_exposes_examples() -> None:
    """Publishes a declarative resource with default sort and examples."""
    app = FastAPI()
    integration = FastAPISQLAlchemyIntegration()
    users = integration.resource(
        User,
        sortable_fields={"name"},
        default_sort="name,desc",
        filter_examples={
            "by_name": {"summary": "By name", "value": "name==demo"},
        },
    )

    @app.get("/users/resource")
    def list_users(
        statement: Annotated[Any, Depends(users.select_dependency())],
    ) -> dict[str, str]:
        return {
            "sql": str(
                statement.compile(compile_kwargs={"literal_binds": True}),
            ),
        }

    response = TestClient(app).get("/users/resource")

    assert response.status_code == 200
    assert "ORDER BY users.name DESC" in response.json()["sql"]

    schema = app.openapi()
    parameters = schema["paths"]["/users/resource"]["get"]["parameters"]
    parameter_map = {parameter["name"]: parameter for parameter in parameters}
    assert (
        parameter_map["filter"]["examples"]["by_name"]["value"] == "name==demo"
    )


def test_resource_dependency_generates_examples_automatically() -> None:
    """Publishes generated examples from declarative resource config."""
    app = FastAPI()
    integration = FastAPISQLAlchemyIntegration()
    users = integration.resource(
        User,
        filterable_fields={"id", "name"},
        sortable_fields={"name"},
        default_sort="-name",
    )

    @app.get("/users/auto-examples")
    def list_users(
        statement: Annotated[Any, Depends(users.select_dependency())],
    ) -> dict[str, str]:
        return {
            "sql": str(
                statement.compile(compile_kwargs={"literal_binds": True}),
            ),
        }

    schema = app.openapi()
    parameters = schema["paths"]["/users/auto-examples"]["get"]["parameters"]
    parameter_map = {parameter["name"]: parameter for parameter in parameters}

    assert (
        parameter_map["filter"]["examples"]["filter_by_id"]["value"] == "id==1"
    )
    assert (
        parameter_map["filter"]["examples"]["filter_by_name"]["value"]
        == "name==demo"
    )
    assert (
        parameter_map["sort"]["examples"]["sort_by_name_asc"]["value"]
        == "name,asc"
    )
    assert (
        parameter_map["sort"]["examples"]["default_sort"]["value"]
        == "name,desc"
    )


def test_resource_applier_dependency_transforms_base_select() -> None:
    """Returns a dependency that applies criteria to a base select."""
    app = FastAPI()
    integration = FastAPISQLAlchemyIntegration()
    users = integration.resource(
        User,
        default_sort="-name",
    )

    @app.get("/users/applier")
    def list_users(
        apply_query: Annotated[Any, Depends(users.applier_dependency())],
    ) -> dict[str, str]:
        statement = apply_query(select(User).where(User.id > 10))
        return {
            "sql": str(
                statement.compile(compile_kwargs={"literal_binds": True}),
            ),
        }

    response = TestClient(app).get("/users/applier")

    assert response.status_code == 200
    sql = response.json()["sql"]
    assert "WHERE users.id > 10" in sql
    assert "ORDER BY users.name DESC" in sql


def test_resource_statement_factory_changes_select_dependency_base() -> None:
    """Uses statement_factory as the base for resource dependencies."""
    app = FastAPI()
    integration = FastAPISQLAlchemyIntegration()
    users = integration.resource(
        User,
        statement_factory=lambda: select(User).where(User.id > 10),
        default_sort="-name",
    )

    @app.get("/users/base-statement")
    def list_users(
        statement: Annotated[Any, Depends(users.select_dependency())],
    ) -> dict[str, str]:
        return {
            "sql": str(
                statement.compile(compile_kwargs={"literal_binds": True}),
            ),
        }

    response = TestClient(app).get("/users/base-statement")

    assert response.status_code == 200
    sql = response.json()["sql"]
    assert "WHERE users.id > 10" in sql
    assert "ORDER BY users.name DESC" in sql
