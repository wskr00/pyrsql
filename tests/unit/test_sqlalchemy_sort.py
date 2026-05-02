"""Unit tests for SQLAlchemy sort compilation and application."""

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

from pyrsql.backends.sqlalchemy import SQLAlchemyBackend
from pyrsql.core.joins import JoinHint
from pyrsql.core.options import SortOptions
from pyrsql.core.sort import Sort


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


def test_backend_applies_simple_order_by_clause() -> None:
    """Applies a simple ascending ORDER BY to a Select."""
    backend = SQLAlchemyBackend()
    statement = Sort.parse("name").apply(
        select(User),
        User,
        backend=backend,
    )
    sql = str(statement)
    assert "ORDER BY" in sql
    assert "user_account.name ASC" in sql


def test_backend_applies_joined_order_by_clause() -> None:
    """Applies ORDER BY across a joined relationship."""
    backend = SQLAlchemyBackend()
    statement = Sort.parse("company.name,desc").apply(
        select(User),
        User,
        backend=backend,
    )
    sql = str(statement)
    assert "JOIN company" in sql
    assert "company.name DESC" in sql


def test_backend_applies_ignore_case_sort_for_string_fields() -> None:
    """Applies lower() for ignore-case sorting on string columns."""
    backend = SQLAlchemyBackend()
    statement = Sort.parse("name,desc,ic").apply(
        select(User),
        User,
        backend=backend,
    )
    sql = str(statement)
    assert "lower(user_account.name) DESC" in sql


def test_backend_applies_field_mapping_for_sort() -> None:
    """Applies sort field mapping before SQLAlchemy translation."""
    backend = SQLAlchemyBackend()
    sort = Sort.parse(
        "companyName,asc",
        options=SortOptions(field_mapping={"companyName": "company.name"}),
    )
    statement = sort.apply(select(User), User, backend=backend)
    sql = str(statement)
    assert "company.name ASC" in sql


def test_backend_ignores_empty_sort_expression() -> None:
    """Leaves the Select unchanged when the sort expression is empty."""
    backend = SQLAlchemyBackend()
    statement = Sort.parse(None).apply(
        select(User),
        User,
        backend=backend,
    )
    assert "ORDER BY" not in str(statement)


def test_backend_applies_function_selector_sort() -> None:
    """Applies a whitelisted SQL function in ORDER BY."""
    backend = SQLAlchemyBackend()
    statement = Sort.parse(
        "@upper[name],asc",
        options=SortOptions(procedure_whitelist=("upper",)),
    ).apply(
        select(User),
        User,
        backend=backend,
    )
    sql = str(statement)
    assert "upper(user_account.name) ASC" in sql


def test_backend_applies_left_join_hint_in_sort() -> None:
    """Applies LEFT OUTER JOIN when requested by sort options."""
    backend = SQLAlchemyBackend()
    statement = Sort.parse(
        "company.name,asc",
        options=SortOptions(
            join_hints={"User.company": JoinHint.LEFT},
        ),
    ).apply(
        select(User),
        User,
        backend=backend,
    )
    sql = str(statement)
    assert "LEFT OUTER JOIN company" in sql


def test_backend_applies_model_field_mapping_in_sort() -> None:
    """Applies model-scoped field aliases during sort resolution."""
    backend = SQLAlchemyBackend()
    statement = Sort.parse(
        "company.companyName,asc",
        options=SortOptions(
            model_field_mapping={Company: {"companyName": "name"}},
        ),
    ).apply(
        select(User),
        User,
        backend=backend,
    )
    sql = str(statement)
    assert "company.name ASC" in sql
