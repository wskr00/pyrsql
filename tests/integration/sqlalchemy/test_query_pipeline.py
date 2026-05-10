"""Integration tests for the SQLAlchemy query pipeline."""

import datetime as dt
from typing import Any

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.sqlalchemy]

sqlalchemy = pytest.importorskip("sqlalchemy")

from sqlalchemy import ForeignKey, String, func, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

import pyrsql
from pyrsql.core.custom import CustomPredicateDefinition
from pyrsql.core.joins import JoinHint
from pyrsql.core.json.options import JSONOptions
from pyrsql.core.options import QueryOptions
from pyrsql.orms.sqlalchemy import SQLAlchemyORM
from pyrsql.orms.sqlalchemy.errors import SQLAlchemyORMError
from pyrsql.parsing.operators import ComparisonOperator


class Base(DeclarativeBase):
    """Base declarative class for ORM tests."""


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
    addresses: Mapped[list["Address"]] = relationship(back_populates="user")


class Address(Base):
    """Test address model for collection relationship filters."""

    __tablename__ = "address"

    id: Mapped[int] = mapped_column(primary_key=True)
    city: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    user: Mapped[User] = relationship(back_populates="addresses")


class Event(Base):
    """Test event model."""

    __tablename__ = "event"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[dt.datetime] = mapped_column()


class JsonEvent(Base):
    """Test event model with JSONB payload."""

    __tablename__ = "json_event"

    id: Mapped[int] = mapped_column(primary_key=True)
    payload: Mapped[dict[str, object]] = mapped_column(postgresql.JSONB)


class JsonDocument(Base):
    """Test event model with JSON payload."""

    __tablename__ = "json_document"

    id: Mapped[int] = mapped_column(primary_key=True)
    payload: Mapped[dict[str, object]] = mapped_column(postgresql.JSON)


def test_orm_applies_simple_where_clause() -> None:
    """Applies a simple comparison to a Select."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse("name==demo")
    statement = orm.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "WHERE" in sql
    assert "user_account.name =" in sql


def test_orm_applies_joined_where_clause() -> None:
    """Applies a joined comparison to a Select."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse("company.name==demo")
    statement = orm.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "JOIN company" in sql
    assert "company.name =" in sql


def test_orm_uses_exists_for_collection_relationship_filter() -> None:
    """Uses any()/has() semantics for collection relationship filters."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse("addresses.city==belem")
    statement = orm.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "EXISTS" in sql
    assert "FROM address" in sql
    assert "JOIN address" not in sql


def test_orm_applies_like_operator() -> None:
    """Applies contains-like semantics for LIKE."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse("name=like=dem")
    statement = orm.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "LIKE" in sql


def test_orm_applies_in_operator() -> None:
    """Applies IN against a list of values."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse("id=in=(1,2,3)")
    statement = orm.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert " IN " in sql


def test_orm_applies_null_check() -> None:
    """Applies a null-check operator."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse("name=nn=")
    statement = orm.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "IS NOT NULL" in sql


def test_orm_interprets_equality_wildcards_by_default() -> None:
    """Uses LIKE semantics for '*' in equality when strict mode is disabled."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse("name==*demo*")
    statement = orm.compile_query(query).apply(select(User), User)
    sql = str(statement.compile(compile_kwargs={"literal_binds": True}))
    assert "LIKE" in sql
    assert "%demo%" in sql


def test_orm_respects_strict_equality_option() -> None:
    """Keeps equality literal when strict equality is enabled."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse(
        "name=='*demo*'",
        options=QueryOptions(strict_equality=True),
    )
    statement = orm.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "LIKE" not in sql
    assert "user_account.name =" in sql


def test_orm_applies_case_insensitive_equality_marker() -> None:
    """Uses case-insensitive equality when '^' is present."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse("name==^demo")
    statement = orm.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "lower(" in sql.lower()
    assert "=" in sql


def test_orm_uses_escape_character_for_like_queries() -> None:
    """Propagates the configured escape character to LIKE expressions."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse(
        "name=like='$%'",
        options=QueryOptions(like_escape_character="$"),
    )
    statement = orm.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "ESCAPE '$'" in sql


def test_orm_applies_function_selector_where_clause() -> None:
    """Applies a whitelisted SQL function in WHERE."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse(
        "@upper[name]==DEMO",
        options=QueryOptions(procedure_whitelist=("upper",)),
    )
    statement = orm.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "upper(user_account.name) =" in sql


def test_orm_applies_distinct_option() -> None:
    """Applies SELECT DISTINCT when query options request it."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse(
        "company.name==demo",
        options=QueryOptions(distinct=True),
    )
    statement = orm.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "SELECT DISTINCT" in sql


def test_orm_applies_left_join_hint_in_where_clause() -> None:
    """Applies LEFT OUTER JOIN when requested by query options."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse(
        "company.name==demo",
        options=QueryOptions(
            join_hints={"User.company": JoinHint.LEFT},
        ),
    )
    statement = orm.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "LEFT OUTER JOIN company" in sql


def test_orm_rejects_right_join_hint() -> None:
    """Rejects unsupported RIGHT join hints in SQLAlchemy."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse(
        "company.name==demo",
        options=QueryOptions(
            join_hints={"User.company": JoinHint.RIGHT},
        ),
    )
    with pytest.raises(SQLAlchemyORMError):
        orm.compile_query(query).apply(select(User), User)


def test_orm_applies_custom_operator_predicate() -> None:
    """Delegates custom operators to ORM-specific predicates."""
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
            ),
        },
    )
    orm = SQLAlchemyORM(
        custom_predicates={
            "all_match": lambda payload: (
                func.lower(payload.expression) == str(payload.values[0]).lower()
            ),
        },
    )
    query = pyrsql.parse("name=all=DEMO", options=options)
    statement = orm.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "lower(user_account.name) =" in sql


def test_orm_uses_core_datetime_conversion_fallback() -> None:
    """Converts plain dates into midnight datetimes via the core registry."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse("created_at==2026-05-02")
    statement = orm.compile_query(query).apply(select(Event), Event)
    compiled = statement.compile()
    assert compiled.params["created_at_1"] == dt.datetime(2026, 5, 2, 0, 0)  # noqa: DTZ001


def test_orm_applies_model_field_mapping_in_where_clause() -> None:
    """Applies model-scoped field aliases during query resolution."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse(
        "company.companyName==demo",
        options=QueryOptions(
            model_field_mapping={Company: {"companyName": "name"}},
        ),
    )
    statement = orm.compile_query(query).apply(select(User), User)
    sql = str(statement)
    assert "company.name =" in sql


def test_orm_enforces_model_field_whitelist() -> None:
    """Rejects fields not listed in a model-specific whitelist."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse(
        "company.name==demo",
        options=QueryOptions(
            model_field_whitelist={Company: frozenset({"id"})},
        ),
    )
    with pytest.raises(SQLAlchemyORMError):
        orm.compile_query(query).apply(select(User), User)


def test_orm_applies_field_specific_converter() -> None:
    """Uses field-path converters before falling back to type converters."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse(
        "created_at==02/05/2026",
        options=QueryOptions(
            field_value_converters={
                "created_at": lambda raw: dt.datetime.strptime(
                    raw,
                    "%d/%m/%Y",
                ).replace(tzinfo=dt.timezone.utc),
            },
        ),
    )
    statement = orm.compile_query(query).apply(select(Event), Event)
    compiled = statement.compile()
    assert compiled.params["created_at_1"] == dt.datetime(
        2026, 5, 2, 0, 0, tzinfo=dt.timezone.utc
    )


def test_orm_applies_model_field_specific_converter() -> None:
    """Uses model-scoped field converters on resolved leaf models."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse(
        "company.name==demo",
        options=QueryOptions(
            model_field_value_converters={
                Company: {"name": lambda raw: raw.upper()},
            },
        ),
    )
    statement = orm.compile_query(query).apply(select(User), User)
    compiled = statement.compile()
    assert compiled.params["name_1"] == "DEMO"


def test_orm_applies_jsonb_where_clause() -> None:
    """Builds JSONB path predicates for nested JSONB selectors."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse("payload.user.id==1")
    statement = orm.compile_query(query).apply(select(JsonEvent), JsonEvent)
    dialect: Any = postgresql.dialect()  # type: ignore[no-untyped-call]
    sql = str(statement.compile(dialect=dialect))
    assert "jsonb_path_exists" in sql
    assert "CAST(%(param_1)s AS JSONPATH)" in sql
    assert "CAST(json_event.payload AS JSONB)" in sql


def test_orm_applies_json_where_clause_via_jsonb_cast() -> None:
    """Builds JSON filters by casting JSON columns to JSONB."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse("payload.name==demo")
    statement = orm.compile_query(query).apply(
        select(JsonDocument),
        JsonDocument,
    )
    dialect: Any = postgresql.dialect()  # type: ignore[no-untyped-call]
    sql = str(statement.compile(dialect=dialect))
    assert "jsonb_path_exists" in sql
    assert "CAST(%(param_1)s AS JSONPATH)" in sql
    assert "CAST(json_document.payload AS JSONB)" in sql


def test_orm_applies_json_array_path_predicate() -> None:
    """Supports nested array element paths through PostgreSQL jsonpath."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse("payload.roles.id==1")
    statement = orm.compile_query(query).apply(select(JsonEvent), JsonEvent)
    dialect: Any = postgresql.dialect()  # type: ignore[no-untyped-call]
    compiled = statement.compile(dialect=dialect)
    assert any(
        str(value) == "$.roles.id ? (@ == 1)"
        for value in compiled.params.values()
    )


def test_orm_applies_json_boolean_predicate() -> None:
    """Normalizes boolean JSON comparisons correctly."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse("payload.active==true")
    statement = orm.compile_query(query).apply(select(JsonEvent), JsonEvent)
    dialect: Any = postgresql.dialect()  # type: ignore[no-untyped-call]
    compiled = statement.compile(dialect=dialect)
    assert any(
        str(value) == "$.active ? (@ == true)"
        for value in compiled.params.values()
    )


def test_orm_applies_json_null_predicate() -> None:
    """Normalizes null JSON comparisons correctly."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse("payload.deleted_at==null")
    statement = orm.compile_query(query).apply(select(JsonEvent), JsonEvent)
    dialect: Any = postgresql.dialect()  # type: ignore[no-untyped-call]
    compiled = statement.compile(dialect=dialect)
    assert any(
        str(value) == "$.deleted_at ? (@ == null)"
        for value in compiled.params.values()
    )


def test_orm_applies_json_in_predicate() -> None:
    """Builds OR-chained jsonpath comparisons for IN."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse("payload.status=in=(1,2,3)")
    statement = orm.compile_query(query).apply(select(JsonEvent), JsonEvent)
    dialect: Any = postgresql.dialect()  # type: ignore[no-untyped-call]
    compiled = statement.compile(dialect=dialect)
    assert any(
        str(value) == "$.status ? ((@ == 1) || (@ == 2) || (@ == 3))"
        for value in compiled.params.values()
    )


def test_orm_applies_json_between_predicate() -> None:
    """Builds range jsonpath comparisons for BETWEEN."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse("payload.score=bt=(10,20)")
    statement = orm.compile_query(query).apply(select(JsonEvent), JsonEvent)
    dialect: Any = postgresql.dialect()  # type: ignore[no-untyped-call]
    compiled = statement.compile(dialect=dialect)
    assert any(
        str(value) == "$.score ? (@ >= 10 && @ <= 20)"
        for value in compiled.params.values()
    )


def test_orm_applies_json_quoted_array_predicate() -> None:
    """Parses quoted JSON arrays as structured JSON values."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse("payload.tags=='[1,2]'")
    statement = orm.compile_query(query).apply(select(JsonEvent), JsonEvent)
    dialect: Any = postgresql.dialect()  # type: ignore[no-untyped-call]
    compiled = statement.compile(dialect=dialect)
    assert compiled.params["param_1"] == "$.tags ? (@ == $value_0)"
    assert compiled.params["param_2"] == {"value_0": [1, 2]}


def test_orm_applies_root_json_array_predicate() -> None:
    """Parses quoted root JSON arrays through the JSON-aware pipeline."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse("payload=='[1,2]'")
    statement = orm.compile_query(query).apply(select(JsonEvent), JsonEvent)
    dialect: Any = postgresql.dialect()  # type: ignore[no-untyped-call]
    compiled = statement.compile(dialect=dialect)
    sql = str(compiled)
    assert " = CAST(%(param_1)s AS JSONB)" in sql
    assert compiled.params["param_1"] == "[1,2]"


def test_orm_applies_json_quoted_object_predicate() -> None:
    """Parses quoted JSON objects as structured JSON values."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse("payload.meta=='{\"id\":1}'")
    statement = orm.compile_query(query).apply(select(JsonEvent), JsonEvent)
    dialect: Any = postgresql.dialect()  # type: ignore[no-untyped-call]
    compiled = statement.compile(dialect=dialect)
    assert compiled.params["param_1"] == "$.meta ? (@ == $value_0)"
    assert compiled.params["param_2"] == {"value_0": {"id": 1}}


def test_orm_applies_root_json_object_predicate() -> None:
    """Parses quoted root JSON objects through the JSON-aware pipeline."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse("payload=='{\"id\":1}'")
    statement = orm.compile_query(query).apply(select(JsonEvent), JsonEvent)
    dialect: Any = postgresql.dialect()  # type: ignore[no-untyped-call]
    compiled = statement.compile(dialect=dialect)
    sql = str(compiled)
    assert " = CAST(%(param_1)s AS JSONB)" in sql
    assert compiled.params["param_1"] == '{"id":1}'


def test_orm_applies_json_datetime_path_predicate() -> None:
    """Builds PostgreSQL datetime jsonpath expressions when enabled."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse(
        "payload.created_at=gt=2026-05-02T10:30:00",
        options=QueryOptions(
            json_options=JSONOptions(use_datetime=True),
        ),
    )
    statement = orm.compile_query(query).apply(
        select(JsonEvent),
        JsonEvent,
    )
    dialect: Any = postgresql.dialect()  # type: ignore[no-untyped-call]
    compiled = statement.compile(dialect=dialect)
    sql = str(compiled)
    assert "@.datetime()" in compiled.params["param_1"]
    assert ".datetime()" in compiled.params["param_1"]
    assert "jsonb_path_exists" in sql
    assert "CAST(%(param_1)s AS JSONPATH)" in sql


def test_orm_applies_json_datetime_tz_path_predicate() -> None:
    """Uses the timezone-aware PostgreSQL function for zoned datetimes."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse(
        "payload.created_at=gt=2026-05-02T10:30:00Z",
        options=QueryOptions(
            json_options=JSONOptions(use_datetime=True),
        ),
    )
    statement = orm.compile_query(query).apply(
        select(JsonEvent),
        JsonEvent,
    )
    dialect: Any = postgresql.dialect()  # type: ignore[no-untyped-call]
    compiled = statement.compile(dialect=dialect)
    sql = str(compiled)
    assert "jsonb_path_exists_tz" in sql
    assert any(
        "@.datetime()" in str(value) for value in compiled.params.values()
    )


def test_orm_uses_custom_json_path_function_names() -> None:
    """Uses custom PostgreSQL JSON path function names from JSONOptions."""
    orm = SQLAlchemyORM()
    query = pyrsql.parse(
        "payload.user.id==1",
        options=QueryOptions(
            json_options=JSONOptions(
                path_exists_function="custom_json_path_exists",
            ),
        ),
    )
    statement = orm.compile_query(query).apply(
        select(JsonEvent),
        JsonEvent,
    )
    dialect: Any = postgresql.dialect()  # type: ignore[no-untyped-call]
    sql = str(statement.compile(dialect=dialect))
    assert "custom_json_path_exists" in sql
    assert "CAST(%(param_1)s AS JSONPATH)" in sql
