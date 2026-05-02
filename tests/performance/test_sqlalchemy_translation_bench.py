"""Performance regression tests for SQLAlchemy ORM translation."""

from __future__ import annotations

from timeit import timeit

import pytest

# pylint: disable=wrong-import-position


sqlalchemy = pytest.importorskip("sqlalchemy")

from sqlalchemy import ForeignKey, String, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

import pyrsql
from pyrsql.orms.sqlalchemy import SQLAlchemyORM

pytestmark = [pytest.mark.performance, pytest.mark.sqlalchemy]


class Base(DeclarativeBase):
    """Base declarative class for performance translation tests."""


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


def test_sqlalchemy_query_application_remains_fast() -> None:
    """Keeps query compilation plus Select application within budget."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse("company.name==demo;name==john*")
    elapsed = timeit(
        lambda: query.apply(select(User), User, orm=orm),
        number=3000,
    )
    average_microseconds = elapsed / 3000 * 1_000_000
    assert average_microseconds < 250.0


def test_sqlalchemy_sort_application_remains_fast() -> None:
    """Keeps sort compilation plus Select application within budget."""
    orm = SQLAlchemyORM()
    sort = pyrsql.Sort.parse("company.name,asc;name,desc")
    elapsed = timeit(
        lambda: sort.apply(select(User), User, orm=orm),
        number=3000,
    )
    average_microseconds = elapsed / 3000 * 1_000_000
    assert average_microseconds < 250.0
