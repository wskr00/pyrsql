"""Unit tests for SQLAlchemy backend translation and application."""

# pylint: disable=wrong-import-position,unsubscriptable-object

import datetime as dt

import pytest

sqlalchemy = pytest.importorskip("sqlalchemy")

from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

import pyrsql
from pyrsql.backends.sqlalchemy import SQLAlchemyBackend
from pyrsql.backends.sqlalchemy.errors import SQLAlchemyBackendError
from pyrsql.core.joins import JoinHint
from pyrsql.core.options import QueryOptions
from pyrsql.core.custom import CustomPredicateDefinition
from pyrsql.parsing.operators import ComparisonOperator


class Base(DeclarativeBase):
    """Base declarative class for backend tests."""


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


class Event(Base):
    """Test event model."""

    __tablename__ = "event"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[dt.datetime] = mapped_column()


def test_backend_applies_simple_where_clause() -> None:
    """Applies a simple comparison to a Select."""
    backend = SQLAlchemyBackend()
    query = pyrsql.parse("name==demo")
    statement = backend.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "WHERE" in sql
    assert "user_account.name =" in sql


def test_backend_applies_joined_where_clause() -> None:
    """Applies a joined comparison to a Select."""
    backend = SQLAlchemyBackend()
    query = pyrsql.parse("company.name==demo")
    statement = backend.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "JOIN company" in sql
    assert "company.name =" in sql


def test_backend_applies_like_operator() -> None:
    """Applies contains-like semantics for LIKE."""
    backend = SQLAlchemyBackend()
    query = pyrsql.parse("name=like=dem")
    statement = backend.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "LIKE" in sql


def test_backend_applies_in_operator() -> None:
    """Applies IN against a list of values."""
    backend = SQLAlchemyBackend()
    query = pyrsql.parse("id=in=(1,2,3)")
    statement = backend.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert " IN " in sql


def test_backend_applies_null_check() -> None:
    """Applies a null-check operator."""
    backend = SQLAlchemyBackend()
    query = pyrsql.parse("name=nn=")
    statement = backend.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "IS NOT NULL" in sql


def test_backend_interprets_equality_wildcards_by_default() -> None:
    """Uses LIKE semantics for '*' in equality when strict mode is disabled."""
    backend = SQLAlchemyBackend()
    query = pyrsql.parse("name==*demo*")
    statement = backend.compile_query(query).apply(select(User), User)
    sql = str(statement.compile(compile_kwargs={"literal_binds": True}))
    assert "LIKE" in sql
    assert "%demo%" in sql


def test_backend_respects_strict_equality_option() -> None:
    """Keeps equality literal when strict equality is enabled."""
    backend = SQLAlchemyBackend()
    query = pyrsql.parse(
        "name=='*demo*'",
        options=QueryOptions(strict_equality=True),
    )
    statement = backend.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "LIKE" not in sql
    assert "user_account.name =" in sql


def test_backend_applies_case_insensitive_equality_marker() -> None:
    """Uses case-insensitive equality when '^' is present."""
    backend = SQLAlchemyBackend()
    query = pyrsql.parse("name==^demo")
    statement = backend.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "lower(" in sql.lower()
    assert "=" in sql


def test_backend_uses_escape_character_for_like_queries() -> None:
    """Propagates the configured escape character to LIKE expressions."""
    backend = SQLAlchemyBackend()
    query = pyrsql.parse(
        "name=like='$%'",
        options=QueryOptions(like_escape_character="$"),
    )
    statement = backend.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "ESCAPE '$'" in sql


def test_backend_applies_function_selector_where_clause() -> None:
    """Applies a whitelisted SQL function in WHERE."""
    backend = SQLAlchemyBackend()
    query = pyrsql.parse(
        "@upper[name]==DEMO",
        options=QueryOptions(procedure_whitelist=("upper",)),
    )
    statement = backend.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "upper(user_account.name) =" in sql


def test_backend_applies_distinct_option() -> None:
    """Applies SELECT DISTINCT when query options request it."""
    backend = SQLAlchemyBackend()
    query = pyrsql.parse(
        "company.name==demo",
        options=QueryOptions(distinct=True),
    )
    statement = backend.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "SELECT DISTINCT" in sql


def test_backend_applies_left_join_hint_in_where_clause() -> None:
    """Applies LEFT OUTER JOIN when requested by query options."""
    backend = SQLAlchemyBackend()
    query = pyrsql.parse(
        "company.name==demo",
        options=QueryOptions(
            join_hints={"User.company": JoinHint.LEFT},
        ),
    )
    statement = backend.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "LEFT OUTER JOIN company" in sql


def test_backend_rejects_right_join_hint() -> None:
    """Rejects unsupported RIGHT join hints in SQLAlchemy."""
    backend = SQLAlchemyBackend()
    query = pyrsql.parse(
        "company.name==demo",
        options=QueryOptions(
            join_hints={"User.company": JoinHint.RIGHT},
        ),
    )
    with pytest.raises(SQLAlchemyBackendError):
        backend.compile_query(query).apply(select(User), User)


def test_backend_applies_custom_operator_predicate() -> None:
    """Delegates custom operators to backend-specific predicates."""
    all_match = ComparisonOperator(
        name="all_match",
        spellings=("=all=",),
        minimum_arguments=1,
        maximum_arguments=1,
    )
    options = QueryOptions(
        custom_predicates={
            "all_match": CustomPredicateDefinition(
                operator=all_match,
                argument_type=str,
            )
        }
    )
    backend = SQLAlchemyBackend(
        custom_predicates={
            "all_match": lambda payload: func.lower(
                payload.expression
            )
            == str(payload.values[0]).lower()
        }
    )
    query = pyrsql.parse("name=all=DEMO", options=options)
    statement = backend.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "lower(user_account.name) =" in sql


def test_backend_uses_core_datetime_conversion_fallback() -> None:
    """Converts plain dates into midnight datetimes via the core registry."""
    backend = SQLAlchemyBackend()
    query = pyrsql.parse("created_at==2026-05-02")
    statement = backend.compile_query(query).apply(select(Event), Event)
    compiled = statement.compile()
    assert compiled.params["created_at_1"] == dt.datetime(2026, 5, 2, 0, 0)


def test_backend_applies_model_field_mapping_in_where_clause() -> None:
    """Applies model-scoped field aliases during query resolution."""
    backend = SQLAlchemyBackend()
    query = pyrsql.parse(
        "company.companyName==demo",
        options=QueryOptions(
            model_field_mapping={Company: {"companyName": "name"}},
        ),
    )
    statement = backend.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "company.name =" in sql


def test_backend_enforces_model_field_whitelist() -> None:
    """Rejects fields not listed in a model-specific whitelist."""
    backend = SQLAlchemyBackend()
    query = pyrsql.parse(
        "company.name==demo",
        options=QueryOptions(
            model_field_whitelist={Company: frozenset({"id"})},
        ),
    )
    with pytest.raises(SQLAlchemyBackendError):
        backend.compile_query(query).apply(select(User), User)


def test_backend_applies_field_specific_converter() -> None:
    """Uses field-path converters before falling back to type converters."""
    backend = SQLAlchemyBackend()
    query = pyrsql.parse(
        "created_at==02/05/2026",
        options=QueryOptions(
            field_value_converters={
                "created_at": lambda raw: dt.datetime.strptime(
                    raw,
                    "%d/%m/%Y",
                )
            }
        ),
    )
    statement = backend.compile_query(query).apply(select(Event), Event)
    compiled = statement.compile()
    assert compiled.params["created_at_1"] == dt.datetime(2026, 5, 2, 0, 0)


def test_backend_applies_model_field_specific_converter() -> None:
    """Uses model-scoped field converters on resolved leaf models."""
    backend = SQLAlchemyBackend()
    query = pyrsql.parse(
        "company.name==demo",
        options=QueryOptions(
            model_field_value_converters={
                Company: {"name": lambda raw: raw.upper()}
            }
        ),
    )
    statement = backend.compile_query(query).apply(select(User), User)
    compiled = statement.compile()
    assert compiled.params["name_1"] == "DEMO"
