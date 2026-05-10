"""Integration tests for the SQLAlchemy page pipeline."""

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.sqlalchemy]

pytest.importorskip("sqlalchemy")

from sqlalchemy import select

from pyrsql.core.page import PageRequest

from .conftest import User, render_sql


def test_orm_applies_limit_and_offset(orm) -> None:
    """Applies LIMIT/OFFSET for a page request."""
    statement = PageRequest.of(2, 25).apply(
        select(User),
        User,
        orm=orm,
    )
    sql = render_sql(statement, literal_binds=True)
    assert "LIMIT 25" in sql
    assert "OFFSET 50" in sql


def test_orm_applies_zero_offset_for_first_page(orm) -> None:
    """Applies zero offset for the first page."""
    statement = PageRequest.of(0, 10).apply(
        select(User),
        User,
        orm=orm,
    )
    sql = render_sql(statement, literal_binds=True)
    assert "LIMIT 10" in sql
    assert "OFFSET 0" in sql
