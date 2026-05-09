"""Shared fixtures for FastAPI + SQLAlchemy integration unit tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.orm import DeclarativeBase

from pyrsql.adapters.fastapi import FastAPICriteriaConfig, RequestCriteria
from pyrsql.core.page import PageRequest
from pyrsql.core.query import Query
from pyrsql.core.sort import Sort
from pyrsql.integrations.fastapi import FastAPISQLAlchemyIntegration
from pyrsql.orms.sqlalchemy import SQLAlchemyORM

if TYPE_CHECKING:
    from sqlalchemy.sql import Select


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


@pytest.fixture(name="sqlalchemy_orm")
def sqlalchemy_orm_fixture() -> SQLAlchemyORM:
    """Provides a real SQLAlchemy ORM adapter for unit-level orchestration."""
    return SQLAlchemyORM()


@pytest.fixture
def integration(
    sqlalchemy_orm: SQLAlchemyORM,
) -> FastAPISQLAlchemyIntegration:
    """Provides a configured FastAPI + SQLAlchemy integration helper."""
    return FastAPISQLAlchemyIntegration(orm=sqlalchemy_orm)


@pytest.fixture
def query_criteria() -> RequestCriteria:
    """Provides query-only request criteria."""
    return RequestCriteria(query=Query.parse("name==demo"))


@pytest.fixture
def full_criteria() -> RequestCriteria:
    """Provides query, sort, and page request criteria."""
    return RequestCriteria(
        query=Query.parse("name==demo"),
        sort=Sort.parse("name,desc"),
        page_request=PageRequest.of(1, 10),
    )


@pytest.fixture
def base_statement() -> Select[Any]:
    """Provides a simple SQLAlchemy select statement for orchestration tests."""
    return select(User)


@pytest.fixture
def fastapi_criteria_config() -> FastAPICriteriaConfig:
    """Provides a reusable FastAPI criteria configuration."""
    return FastAPICriteriaConfig(default_page_size=20)
