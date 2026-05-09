"""Shared fixtures and mapped test models for SQLAlchemy ORM unit tests."""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from pyrsql.orms.sqlalchemy.introspection import SQLAlchemyModelInspector
from pyrsql.orms.sqlalchemy.json_path import SQLAlchemyJSONPathExpressionBuilder
from pyrsql.orms.sqlalchemy.resolver import SQLAlchemyPathResolver


class Base(DeclarativeBase):
    """Base declarative class for SQLAlchemy ORM unit tests."""


class Company(Base):
    """Test company model."""

    __tablename__ = "company"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))


class User(Base):
    """Test user model."""

    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"))
    company: Mapped[Company] = relationship()
    addresses: Mapped[list[Address]] = relationship(back_populates="user")


class Address(Base):
    """Test address model for collection relationships."""

    __tablename__ = "address"

    id: Mapped[int] = mapped_column(primary_key=True)
    city: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    user: Mapped[User] = relationship(back_populates="addresses")


class Event(Base):
    """Test event model with JSON content."""

    __tablename__ = "event"

    id: Mapped[int] = mapped_column(primary_key=True)
    payload: Mapped[dict[str, object]] = mapped_column(postgresql.JSONB)


@pytest.fixture
def postgresql_dialect() -> Any:
    """Provides a PostgreSQL dialect instance for SQL compilation tests."""
    return postgresql.dialect()  # type: ignore[no-untyped-call]


@pytest.fixture
def model_inspector() -> SQLAlchemyModelInspector:
    """Provides a model inspector for metadata resolution tests."""
    return SQLAlchemyModelInspector()


@pytest.fixture
def path_resolver() -> SQLAlchemyPathResolver:
    """Provides a path resolver for ORM field-path tests."""
    return SQLAlchemyPathResolver()


@pytest.fixture
def json_path_builder() -> SQLAlchemyJSONPathExpressionBuilder:
    """Provides a JSON path expression builder for SQL generation tests."""
    return SQLAlchemyJSONPathExpressionBuilder()
