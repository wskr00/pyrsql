# Async Flows

`pyrsql` itself does not perform database I/O. It builds SQLAlchemy statements
and criteria objects. Because of that, the same compiled `Select` objects work
for both:

- synchronous `Session`
- asynchronous `AsyncSession`

The async work happens in your application when you execute the statement.

## What async support means in pyrsql

`pyrsql` is async-compatible, not async-only:

- the core query/sort/page APIs are synchronous object transformations
- the FastAPI adapter parses request data synchronously
- async execution happens when your app runs the generated SQLAlchemy
  statements through `AsyncSession`

This keeps the same query pipeline usable in both sync and async applications.

## SQLAlchemy async session

```python
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

engine = create_async_engine(
    "sqlite+aiosqlite:///./app.db",
)
SessionFactory = async_sessionmaker(
    engine,
    expire_on_commit=False,
)

async def get_async_session():
    async with SessionFactory() as session:
        yield session
```

## FastAPI async route

```python
from typing import Annotated, Any

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from pyrsql.integrations.fastapi import FastAPISQLAlchemyIntegration

app = FastAPI()
integration = FastAPISQLAlchemyIntegration()

@app.get("/users")
async def list_users(
    stmt: Annotated[Any, Depends(integration.select_dependency(User))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    result = await session.scalars(stmt)
    return result.all()
```

The dependency is still synchronous from `pyrsql`'s perspective because it only
parses request data and builds one SQLAlchemy `Select`.

## Count and pagination

```python
@app.get("/users/count")
async def count_users(
    stmt: Annotated[Any, Depends(integration.count_select_dependency(User))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    return {"count": await session.scalar(stmt)}

@app.get("/users/paginated")
async def paginated_users(
    bundle: Annotated[
        Any,
        Depends(integration.paginated_select_dependency(User)),
    ],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    items = (await session.scalars(bundle.statement)).all()
    total = await session.scalar(bundle.count_statement)
    return {"items": items, "total": total}
```

## Direct async execution without FastAPI

```python
from sqlalchemy import select

import pyrsql

query = pyrsql.parse("name==demo")
stmt = query.apply(select(User), User, orm=sqlalchemy_orm)

async with SessionFactory() as session:
    result = await session.scalars(stmt)
    users = result.all()
```

## Constraints and guidance

- Do not share one `AsyncSession` across concurrent tasks.
- `pyrsql` can safely reuse immutable options/configuration objects across async
  requests.
- The integration layer only builds statements; it does not manage session
  lifetime.
- Parse and page-validation failures still become structured `HTTP 400`
  responses in FastAPI.
- Semantic and backend integration failures still become structured `HTTP 422`
  responses in FastAPI.

## Free-threaded note

Async support and free-threaded support are separate concerns:

- async support is about how your application executes the generated
  SQLAlchemy statements
- free-threaded support is about protecting shared mutable caches used by the
  integration and SQLAlchemy helper layers

You can use async routes without a free-threaded Python build, and you can
benefit from free-threaded-safe cache handling in synchronous applications too.

## Test coverage

The test suite includes async coverage at three levels:

- FastAPI adapter behavior on `async def` routes
- SQLAlchemy pipeline execution with `AsyncSession`
- FastAPI + SQLAlchemy end-to-end async integration
