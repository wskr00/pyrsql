"""Shared fixtures for SQLAlchemy integration tests."""

from __future__ import annotations

import datetime as dt

import pytest

pytest.importorskip("sqlalchemy")

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)

from pyrsql.orms.sqlalchemy import SQLAlchemyORM

if TYPE_CHECKING:
    from sqlalchemy.engine import Dialect as _Dialect


class Base(DeclarativeBase):
    """Base declarative class for integration-test models."""


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
    """Test address model for collection relationship filters."""

    __tablename__ = "address"

    id: Mapped[int] = mapped_column(primary_key=True)
    city: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    user: Mapped[User] = relationship(back_populates="addresses")


class Event(Base):
    """Test event model with datetime column."""

    __tablename__ = "event"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[dt.datetime] = mapped_column()


class JsonEvent(Base):
    """Test event model with JSONB payload."""

    __tablename__ = "json_event"

    id: Mapped[int] = mapped_column(primary_key=True)
    payload: Mapped[dict[str, object]] = mapped_column(postgresql.JSONB)


class JsonDocument(Base):
    """Test document model with JSON payload."""

    __tablename__ = "json_document"

    id: Mapped[int] = mapped_column(primary_key=True)
    payload: Mapped[dict[str, object]] = mapped_column(postgresql.JSON)


@pytest.fixture
def orm() -> SQLAlchemyORM:
    """Provides a fresh SQLAlchemy ORM instance for each test."""
    return SQLAlchemyORM()


@pytest.fixture
def pg_dialect() -> _Dialect:
    """Provides a PostgreSQL dialect instance for SQL rendering."""
    return postgresql.dialect()


def render_sql(
    statement: Any,
    *,
    dialect: _Dialect | None = None,
    literal_binds: bool = False,
) -> str:
    """Compiles and renders a SQLAlchemy statement as a string.

    When called without arguments the statement is rendered via ``str()``
    (the default dialect).  Pass ``literal_binds=True`` to inline bound
    parameter values, or ``dialect=...`` for dialect-specific output.
    """
    compile_kwargs: dict[str, Any] = {}
    if dialect is not None:
        compile_kwargs["dialect"] = dialect
    if literal_binds:
        compile_kwargs["compile_kwargs"] = {"literal_binds": True}
    if compile_kwargs:
        return str(statement.compile(**compile_kwargs))
    return str(statement)
