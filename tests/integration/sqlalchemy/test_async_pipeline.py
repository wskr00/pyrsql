"""Async integration tests for SQLAlchemy statement execution."""

import pytest

pytest.importorskip("aiosqlite")
pytest.importorskip("sqlalchemy")
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from tests.functional.fastapi_sqlalchemy.conftest import Base, User

import pyrsql
from pyrsql.core.page import PageRequest
from pyrsql.core.sort import Sort

pytestmark = [
    pytest.mark.integration,
    pytest.mark.sqlalchemy,
    pytest.mark.anyio,
]


def _database_url(database_path: object) -> str:
    """Builds one SQLite async database URL for a test."""
    return f"sqlite+aiosqlite:///{database_path}"


async def _create_schema(database_path: object):
    """Creates one async engine and initializes the schema."""
    engine = create_async_engine(_database_url(database_path))
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine


async def _seed_users(session_factory: async_sessionmaker, *names: str) -> None:
    """Seeds test rows through an AsyncSession."""
    async with session_factory() as session:
        session.add_all([User(name=name) for name in names])
        await session.commit()


async def test_query_statement_executes_with_async_session(
    tmp_path,
) -> None:
    """Executes a compiled pyrsql query through AsyncSession."""
    database_path = tmp_path / "query.db"
    engine = await _create_schema(database_path)
    try:
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        await _seed_users(session_factory, "demo", "maria")
        orm = pyrsql.orms.sqlalchemy.SQLAlchemyORM()
        statement = pyrsql.parse("name==demo").apply(
            select(User),
            User,
            orm=orm,
        )

        async with session_factory() as session:
            users = (await session.scalars(statement)).all()

        assert [user.name for user in users] == ["demo"]
    finally:
        await engine.dispose()


async def test_sort_statement_executes_with_async_session(
    tmp_path,
) -> None:
    """Executes a compiled pyrsql sort through AsyncSession."""
    database_path = tmp_path / "sort.db"
    engine = await _create_schema(database_path)
    try:
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        await _seed_users(session_factory, "demo", "zoe", "maria")
        orm = pyrsql.orms.sqlalchemy.SQLAlchemyORM()
        statement = Sort.parse("name,desc").apply(select(User), User, orm=orm)

        async with session_factory() as session:
            users = (await session.scalars(statement)).all()

        assert [user.name for user in users] == ["zoe", "maria", "demo"]
    finally:
        await engine.dispose()


async def test_page_statement_executes_with_async_session(
    tmp_path,
) -> None:
    """Executes a compiled pyrsql page request through AsyncSession."""
    database_path = tmp_path / "page.db"
    engine = await _create_schema(database_path)
    try:
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        await _seed_users(session_factory, "ana", "bia", "cai", "dio")
        orm = pyrsql.orms.sqlalchemy.SQLAlchemyORM()
        statement = Sort.parse("name,asc").apply(select(User), User, orm=orm)
        paged_statement = PageRequest.of(1, 2).apply(statement, User, orm=orm)

        async with session_factory() as session:
            users = (await session.scalars(paged_statement)).all()

        assert [user.name for user in users] == ["cai", "dio"]
    finally:
        await engine.dispose()
