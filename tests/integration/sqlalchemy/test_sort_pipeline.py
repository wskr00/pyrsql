"""Integration tests for the SQLAlchemy sort pipeline."""

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.sqlalchemy]

pytest.importorskip("sqlalchemy")

from sqlalchemy import select

from pyrsql.core.joins import JoinHint
from pyrsql.core.json.options import JSONOptions, JSONSortScalarType
from pyrsql.core.options import SortOptions
from pyrsql.core.sort import Sort
from pyrsql.orms.sqlalchemy import SQLAlchemyJSONSupportError

from .conftest import Company, JsonEvent, User, render_sql


def test_orm_applies_simple_order_by_clause(orm) -> None:
    """Applies a simple ascending ORDER BY to a Select."""
    statement = Sort.parse("name").apply(
        select(User),
        User,
        orm=orm,
    )
    sql = render_sql(statement)
    assert "ORDER BY" in sql
    assert "user_account.name ASC" in sql


def test_orm_applies_joined_order_by_clause(orm) -> None:
    """Applies ORDER BY across a joined relationship."""
    statement = Sort.parse("company.name,desc").apply(
        select(User),
        User,
        orm=orm,
    )
    sql = render_sql(statement)
    assert "JOIN company" in sql
    assert "company.name DESC" in sql


def test_orm_applies_ignore_case_sort_for_string_fields(orm) -> None:
    """Applies lower() for ignore-case sorting on string columns."""
    statement = Sort.parse("name,desc,ic").apply(
        select(User),
        User,
        orm=orm,
    )
    sql = render_sql(statement)
    assert "lower(user_account.name) DESC" in sql


def test_orm_applies_field_mapping_for_sort(orm) -> None:
    """Applies sort field mapping before SQLAlchemy translation."""
    sort = Sort.parse(
        "companyName,asc",
        options=SortOptions(field_mapping={"companyName": "company.name"}),
    )
    statement = sort.apply(select(User), User, orm=orm)
    sql = render_sql(statement)
    assert "company.name ASC" in sql


def test_orm_ignores_empty_sort_expression(orm) -> None:
    """Leaves the Select unchanged when the sort expression is empty."""
    statement = Sort.parse(None).apply(
        select(User),
        User,
        orm=orm,
    )
    assert "ORDER BY" not in render_sql(statement)


def test_orm_applies_function_selector_sort(orm) -> None:
    """Applies a whitelisted SQL function in ORDER BY."""
    statement = Sort.parse(
        "@upper[name],asc",
        options=SortOptions(procedure_whitelist=("upper",)),
    ).apply(
        select(User),
        User,
        orm=orm,
    )
    sql = render_sql(statement)
    assert "upper(user_account.name) ASC" in sql


def test_orm_applies_left_join_hint_in_sort(orm) -> None:
    """Applies LEFT OUTER JOIN when requested by sort options."""
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
    sql = render_sql(statement)
    assert "LEFT OUTER JOIN company" in sql


def test_orm_applies_model_field_mapping_in_sort(orm) -> None:
    """Applies model-scoped field aliases during sort resolution."""
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
    sql = render_sql(statement)
    assert "company.name ASC" in sql


def test_orm_applies_json_sort_clause(orm, pg_dialect) -> None:
    """Builds JSON path extraction operators for JSON sort expressions."""
    statement = Sort.parse("payload.user.id,asc").apply(
        select(JsonEvent),
        JsonEvent,
        orm=orm,
    )
    sql = render_sql(statement, dialect=pg_dialect)
    assert "#>>" in sql
    assert "payload" in sql


def test_orm_applies_typed_json_numeric_sort_clause(orm, pg_dialect) -> None:
    """Applies configured numeric casts for JSON sort expressions."""
    statement = Sort.parse(
        "payload.user.id,asc",
        options=SortOptions(
            json_options=JSONOptions(
                sort_field_types={
                    "payload.user.id": JSONSortScalarType.INTEGER,
                },
            ),
        ),
    ).apply(
        select(JsonEvent),
        JsonEvent,
        orm=orm,
    )
    sql = render_sql(statement, dialect=pg_dialect)
    assert "CAST(" in sql
    assert " AS INTEGER)" in sql


def test_orm_rejects_root_json_sort_without_explicit_configuration(orm) -> None:
    """Rejects ambiguous whole-document JSON sorting by default."""
    with pytest.raises(SQLAlchemyJSONSupportError, match="whole JSON document"):
        Sort.parse("payload,asc").apply(
            select(JsonEvent),
            JsonEvent,
            orm=orm,
        )


def test_orm_allows_root_json_sort_with_explicit_text_configuration(
    orm,
    pg_dialect,
) -> None:
    """Allows whole-document JSON sort only with explicit text semantics."""
    statement = Sort.parse(
        "payload,asc",
        options=SortOptions(
            json_options=JSONOptions(
                sort_field_types={
                    "payload": JSONSortScalarType.TEXT,
                },
            ),
        ),
    ).apply(
        select(JsonEvent),
        JsonEvent,
        orm=orm,
    )
    sql = render_sql(statement, dialect=pg_dialect)
    assert "CAST(CAST(json_event.payload AS JSONB) AS TEXT) ASC" in sql
