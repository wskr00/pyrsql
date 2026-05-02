"""Unit tests for SQLAlchemy sort compilation and application."""

# pylint: disable=wrong-import-position,unsubscriptable-object

from typing import Any

import pytest

sqlalchemy = pytest.importorskip("sqlalchemy")

from sqlalchemy import ForeignKey, String, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from pyrsql.core.joins import JoinHint
from pyrsql.core.options import SortOptions
from pyrsql.core.sort import Sort
from pyrsql.orms.sqlalchemy import SQLAlchemyORM


class Base(DeclarativeBase):
    """Base declarative class for sort tests."""


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


class JsonEvent(Base):
    """Test event model with JSON payload for sorting."""

    __tablename__ = "json_event"

    id: Mapped[int] = mapped_column(primary_key=True)
    payload: Mapped[dict[str, object]] = mapped_column(postgresql.JSONB)


def test_orm_applies_simple_order_by_clause() -> None:
    """Applies a simple ascending ORDER BY to a Select."""
    orm = SQLAlchemyORM()
    statement = Sort.parse("name").apply(
        select(User),
        User,
        orm=orm,
    )
    sql = str(statement)
    assert "ORDER BY" in sql
    assert "user_account.name ASC" in sql


def test_orm_applies_joined_order_by_clause() -> None:
    """Applies ORDER BY across a joined relationship."""
    orm = SQLAlchemyORM()
    statement = Sort.parse("company.name,desc").apply(
        select(User),
        User,
        orm=orm,
    )
    sql = str(statement)
    assert "JOIN company" in sql
    assert "company.name DESC" in sql


def test_orm_applies_ignore_case_sort_for_string_fields() -> None:
    """Applies lower() for ignore-case sorting on string columns."""
    orm = SQLAlchemyORM()
    statement = Sort.parse("name,desc,ic").apply(
        select(User),
        User,
        orm=orm,
    )
    sql = str(statement)
    assert "lower(user_account.name) DESC" in sql


def test_orm_applies_field_mapping_for_sort() -> None:
    """Applies sort field mapping before SQLAlchemy translation."""
    orm = SQLAlchemyORM()
    sort = Sort.parse(
        "companyName,asc",
        options=SortOptions(field_mapping={"companyName": "company.name"}),
    )
    statement = sort.apply(select(User), User, orm=orm)
    sql = str(statement)
    assert "company.name ASC" in sql


def test_orm_ignores_empty_sort_expression() -> None:
    """Leaves the Select unchanged when the sort expression is empty."""
    orm = SQLAlchemyORM()
    statement = Sort.parse(None).apply(
        select(User),
        User,
        orm=orm,
    )
    assert "ORDER BY" not in str(statement)


def test_orm_applies_function_selector_sort() -> None:
    """Applies a whitelisted SQL function in ORDER BY."""
    orm = SQLAlchemyORM()
    statement = Sort.parse(
        "@upper[name],asc",
        options=SortOptions(procedure_whitelist=("upper",)),
    ).apply(
        select(User),
        User,
        orm=orm,
    )
    sql = str(statement)
    assert "upper(user_account.name) ASC" in sql


def test_orm_applies_left_join_hint_in_sort() -> None:
    """Applies LEFT OUTER JOIN when requested by sort options."""
    orm = SQLAlchemyORM()
    statement = Sort.parse(
        "company.name,asc",
        options=SortOptions(
            join_hints={"User.company": JoinHint.LEFT},
        ),
    ).apply(
        select(User),
        User,
        orm=orm,
    )
    sql = str(statement)
    assert "LEFT OUTER JOIN company" in sql


def test_orm_applies_model_field_mapping_in_sort() -> None:
    """Applies model-scoped field aliases during sort resolution."""
    orm = SQLAlchemyORM()
    statement = Sort.parse(
        "company.companyName,asc",
        options=SortOptions(
            model_field_mapping={Company: {"companyName": "name"}},
        ),
    ).apply(
        select(User),
        User,
        orm=orm,
    )
    sql = str(statement)
    assert "company.name ASC" in sql


def test_orm_applies_json_sort_clause() -> None:
    """Builds JSON path extraction operators for JSON sort expressions."""
    orm = SQLAlchemyORM()
    statement = Sort.parse("payload.user.id,asc").apply(
        select(JsonEvent),
        JsonEvent,
        orm=orm,
    )
    dialect: Any = postgresql.dialect()  # type: ignore[no-untyped-call]
    sql = str(statement.compile(dialect=dialect))
    assert "#>>" in sql
    assert "payload" in sql
