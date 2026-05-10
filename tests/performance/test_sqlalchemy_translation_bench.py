"""Performance regression tests for SQLAlchemy ORM translation."""

from __future__ import annotations

from timeit import timeit

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import select

import pyrsql
from pyrsql.core.page import PageRequest
from pyrsql.orms.sqlalchemy import SQLAlchemyORM

from .conftest import User

pytestmark = [pytest.mark.performance, pytest.mark.sqlalchemy]


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


def test_sqlalchemy_page_application_remains_fast() -> None:
    """Keeps page compilation plus Select application within budget."""
    orm = SQLAlchemyORM()
    page = PageRequest.of(2, 25)
    elapsed = timeit(
        lambda: page.apply(select(User), User, orm=orm),
        number=5000,
    )
    average_microseconds = elapsed / 5000 * 1_000_000
    assert average_microseconds < 100.0
