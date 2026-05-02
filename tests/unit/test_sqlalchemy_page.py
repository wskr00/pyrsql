"""Unit tests for SQLAlchemy pagination compilation and application."""

# pylint: disable=wrong-import-position,unsubscriptable-object

import pytest

sqlalchemy = pytest.importorskip("sqlalchemy")

from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from pyrsql.orms.sqlalchemy import SQLAlchemyORM
from pyrsql.core.page import PageRequest


class Base(DeclarativeBase):
    """Base declarative class for page tests."""


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


def test_orm_applies_limit_and_offset() -> None:
    """Applies LIMIT/OFFSET for a page request."""
    orm = SQLAlchemyORM()
    statement = PageRequest.of(2, 25).apply(
        select(User),
        User,
        orm=orm,
    )
    sql = str(statement.compile(compile_kwargs={"literal_binds": True}))
    assert "LIMIT 25" in sql
    assert "OFFSET 50" in sql


def test_orm_applies_zero_offset_for_first_page() -> None:
    """Applies zero offset for the first page."""
    orm = SQLAlchemyORM()
    statement = PageRequest.of(0, 10).apply(
        select(User),
        User,
        orm=orm,
    )
    sql = str(statement.compile(compile_kwargs={"literal_binds": True}))
    assert "LIMIT 10" in sql
    assert "OFFSET 0" in sql
