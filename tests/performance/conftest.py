"""Shared fixtures and test data for performance regression tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from pyrsql.orms.sqlalchemy import SQLAlchemyORM

if TYPE_CHECKING:
    from sqlalchemy.engine import Dialect as _Dialect

DATETIME_TEXT = "2026-05-02T10:30:45.123456+00:00"
DATE_TEXT = "2026-05-02"
MEDIUM_QUERY = "company.name==demo;name==john*;addresses.city==belem"
COMPLEX_QUERY = (
    "(company.name==demo,name==john*);"
    "(@upper[name]==JOHN;addresses.city==belem)"
)
FUNCTION_SELECTOR = "@concat[@upper[name]|#123|##raw]"
QUERY_TEXT = "@upper[name]==JOHN;company.name==demo;addresses.city==belem"
SORT_TEXT = "@upper[name],asc;company.name,desc;name,asc,ic"
QUOTED_JSON_OBJECT = '{"user":{"id":1,"name":"demo"},"active":true}'
QUOTED_JSON_ARRAY = '[1,2,3,4,{"nested":true}]'


class _Base(DeclarativeBase):
    """Base declarative class for performance benchmark models."""


class Company(_Base):
    """Test company model."""

    __tablename__ = "company"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))


class User(_Base):
    """Test user model."""

    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"))
    company: Mapped[Company] = relationship()


@pytest.fixture(scope="session")
def sqlalchemy_orm() -> SQLAlchemyORM:
    """Provides a session-scoped SQLAlchemy ORM for benchmarks."""
    return SQLAlchemyORM()


@pytest.fixture(scope="session")
def pg_dialect() -> _Dialect:
    """Provides a PostgreSQL dialect instance for JSON benchmarks."""
    return postgresql.dialect()  # type: ignore[no-untyped-call]
