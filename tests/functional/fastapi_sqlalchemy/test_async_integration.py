"""Async functional tests for the FastAPI + SQLAlchemy integration."""

from typing import Annotated, Any

import pytest

pytest.importorskip("aiosqlite")
pytest.importorskip("fastapi")
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from pyrsql.integrations.fastapi import FastAPISQLAlchemyIntegration

from .conftest import Base, User

pytestmark = [
    pytest.mark.functional,
    pytest.mark.fastapi,
    pytest.mark.sqlalchemy,
    pytest.mark.anyio,
]


def _database_url(database_path: object) -> str:
    """Builds one SQLite async database URL for a test."""
    return f"sqlite+aiosqlite:///{database_path}"


async def _create_engine(
    database_path: object,
) -> Any:
    """Creates one async SQLAlchemy engine for a test database."""
    engine = create_async_engine(_database_url(database_path))
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return engine


async def _insert_users(
    session_factory: async_sessionmaker[Any],
    *names: str,
) -> None:
    """Inserts test users using one async session factory."""
    async with session_factory() as session:
        session.add_all([User(name=name) for name in names])
        await session.commit()


def _build_app(
    session_factory: async_sessionmaker[Any],
) -> FastAPI:
    """Builds one FastAPI app wired to an async SQLAlchemy session."""
    app = FastAPI()
    integration = FastAPISQLAlchemyIntegration()

    async def get_session():
        async with session_factory() as session:
            yield session

    @app.get("/users")
    async def list_users(
        statement: Annotated[Any, Depends(integration.select_dependency(User))],
        session: Annotated[Any, Depends(get_session)],
    ) -> list[str]:
        users = (await session.scalars(statement)).all()
        return [user.name for user in users]

    @app.get("/users/count")
    async def count_users(
        statement: Annotated[
            Any, Depends(integration.count_select_dependency(User))
        ],
        session: Annotated[Any, Depends(get_session)],
    ) -> dict[str, int]:
        total = await session.scalar(statement)
        assert total is not None
        return {"count": total}

    @app.get("/users/paginated")
    async def paginated_users(
        bundle: Annotated[
            Any, Depends(integration.paginated_select_dependency(User))
        ],
        session: Annotated[Any, Depends(get_session)],
    ) -> dict[str, object]:
        users = (await session.scalars(bundle.statement)).all()
        total = await session.scalar(bundle.count_statement)
        assert total is not None
        return {
            "names": [user.name for user in users],
            "count": total,
        }

    @app.get("/users/resource")
    async def resource_users(
        statement: Annotated[
            Any,
            Depends(
                integration.resource(
                    User,
                    sortable_fields={"name"},
                    default_sort="-name",
                ).select_dependency()
            ),
        ],
        session: Annotated[Any, Depends(get_session)],
    ) -> list[str]:
        users = (await session.scalars(statement)).all()
        return [user.name for user in users]

    return app


@pytest.mark.parametrize(
    ("params", "expected_names"),
    [
        pytest.param(
            {"filter": "name==demo", "sort": "name,asc"},
            ["demo"],
            id="filtered-select",
        ),
        pytest.param(
            {"sort": "name,desc", "size": 2},
            ["zoe", "maria"],
            id="sorted-and-paged-select",
        ),
    ],
)
async def test_async_select_dependency_returns_expected_rows(
    tmp_path,
    *,
    params: dict[str, object],
    expected_names: list[str],
) -> None:
    """Returns rows through AsyncSession using the select dependency."""
    database_path = tmp_path / "select.db"
    engine = await _create_engine(database_path)
    try:
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        await _insert_users(session_factory, "demo", "maria", "zoe")
        app = _build_app(session_factory)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/users", params=params)

        assert response.status_code == 200
        assert response.json() == expected_names
    finally:
        await engine.dispose()


async def test_async_count_select_dependency_returns_filtered_count(
    tmp_path,
) -> None:
    """Returns a filtered count through AsyncSession."""
    database_path = tmp_path / "count.db"
    engine = await _create_engine(database_path)
    try:
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        await _insert_users(session_factory, "demo", "demo", "zoe")
        app = _build_app(session_factory)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/users/count",
                params={"filter": "name==demo", "sort": "name,asc"},
            )

        assert response.status_code == 200
        assert response.json() == {"count": 2}
    finally:
        await engine.dispose()


async def test_async_paginated_select_dependency_returns_rows_and_count(
    tmp_path,
) -> None:
    """Returns paginated rows and total count through AsyncSession."""
    database_path = tmp_path / "paginated.db"
    engine = await _create_engine(database_path)
    try:
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        await _insert_users(session_factory, "demo", "maria", "zoe")
        app = _build_app(session_factory)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/users/paginated",
                params={"sort": "name,asc", "size": 2},
            )

        assert response.status_code == 200
        assert response.json() == {
            "names": ["demo", "maria"],
            "count": 3,
        }
    finally:
        await engine.dispose()


async def test_async_resource_dependency_applies_default_sort(
    tmp_path,
) -> None:
    """Applies resource default sort in an async FastAPI route."""
    database_path = tmp_path / "resource.db"
    engine = await _create_engine(database_path)
    try:
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        await _insert_users(session_factory, "demo", "maria", "zoe")
        app = _build_app(session_factory)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/users/resource")

        assert response.status_code == 200
        assert response.json() == ["zoe", "maria", "demo"]
    finally:
        await engine.dispose()
