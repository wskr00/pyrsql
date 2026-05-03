"""Functional tests for the FastAPI + SQLAlchemy integration helper."""

from __future__ import annotations

# pylint: disable=wrong-import-position

from typing import Any

import pytest

pytest.importorskip("fastapi")
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Column, Integer, String
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
        statement: Any = Depends(integration.select_dependency(User)),
    ) -> dict[str, str]:
        return {
            "sql": str(
                statement.compile(compile_kwargs={"literal_binds": True})
            )
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
        statement: Any = Depends(integration.count_select_dependency(User)),
    ) -> dict[str, str]:
        return {
            "sql": str(
                statement.compile(compile_kwargs={"literal_binds": True})
            )
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
        bundle: Any = Depends(integration.paginated_select_dependency(User)),
    ) -> dict[str, str]:
        return {
            "statement": str(
                bundle.statement.compile(
                    compile_kwargs={"literal_binds": True}
                )
            ),
            "count_statement": str(
                bundle.count_statement.compile(
                    compile_kwargs={"literal_binds": True}
                )
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
