# Quickstart

## Install

```bash
pip install pyrsql                    # core only
pip install pyrsql[sqlalchemy]        # with SQLAlchemy
pip install pyrsql[fastapi]           # with FastAPI
pip install pyrsql[fastapi,sqlalchemy]  # both
```

## Recommended: FastAPI + SQLAlchemy

For a FastAPI application backed by SQLAlchemy, start with the integration.
It owns the public query contract for one model and gives routes a ready-to-use
SQLAlchemy statement.

```python
from typing import Annotated, Any

from fastapi import Depends, FastAPI

from pyrsql.integrations.fastapi import FastAPISQLAlchemyIntegration

app = FastAPI()
integration = FastAPISQLAlchemyIntegration()
users = integration.resource(
    User,
    filterable_fields={"id", "name"},
    sortable_fields={"name"},
    default_sort="name,asc",
)

@app.get("/users")
def list_users(
    stmt: Annotated[Any, Depends(users.select_dependency())],
):
    return {"sql": str(stmt)}
```

Clients can use `filter`, `sort`, `page`, and `size`. The integration also
offers count and paginated dependencies. See [FastAPI + SQLAlchemy](usage/fastapi-sqlalchemy.md)
for the complete route API.

## Building blocks

The following sections show the lower-level APIs used by the integration. They
are useful for non-FastAPI applications or when you need direct control.

## Filter

```python
from pyrsql import Query

Query.parse("name==demo")            # equal
Query.parse("age=gt=18")             # greater than
Query.parse("id=in=(1,2,3)")         # IN
Query.parse("name=like=demo*")       # LIKE
Query.parse("score=bt=(10,20)")      # BETWEEN
Query.parse("name==demo;age=gt=18")  # AND
Query.parse("name==demo,age=gt=18")  # OR
```

## Sort

```python
from pyrsql import Sort

Sort.parse("name")              # ascending
Sort.parse("name,desc")         # descending
Sort.parse("name,asc;company.name,desc")  # multi-field
```

## Paginate

```python
from pyrsql import PageRequest

PageRequest.of(0, 25)   # first page, 25 items
PageRequest.of(2, 25)   # third page, 25 items
```

## SQLAlchemy

```python
from pyrsql import PageRequest, Query, Sort
from pyrsql.orms.sqlalchemy import SQLAlchemyORM
from sqlalchemy import select

orm = SQLAlchemyORM()

stmt = select(User)
stmt = Query.parse("name==demo;company.name==acme*").apply(
    stmt,
    User,
    orm=orm,
)
stmt = Sort.parse("name,asc;company.name,desc").apply(stmt, User, orm=orm)
stmt = PageRequest.of(0, 25).apply(stmt, User, orm=orm)
```

## FastAPI

```python
from typing import Annotated

from fastapi import Depends, FastAPI
from pyrsql.adapters.fastapi import RequestCriteria, criteria_dependency

app = FastAPI()

@app.get("/items")
def list_items(
    criteria: Annotated[RequestCriteria, Depends(criteria_dependency())],
):
    return {"is_empty": criteria.is_empty}
```

Query params `filter`, `sort`, `page`, `size` are extracted automatically.
Parse and page-validation errors become structured `HTTP 400` responses.
Semantic and backend integration errors become structured `HTTP 422`
responses.

## Direct integration dependency

```python
from typing import Annotated, Any

from fastapi import Depends, FastAPI

from pyrsql.integrations.fastapi import FastAPISQLAlchemyIntegration

app = FastAPI()
integration = FastAPISQLAlchemyIntegration()

@app.get("/users")
def list_users(
    stmt: Annotated[Any, Depends(integration.select_dependency(User))],
):
    return {"sql": str(stmt)}
```

Also available:

- `count_select_dependency(...)`
- `paginated_select_dependency(...)`
- declarative `resource(...)`

## Async execution

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

`pyrsql` builds statements only; your application decides whether to execute
them through sync or async SQLAlchemy sessions.

## Notes

- `pyrsql` builds statements and criteria objects only. Your application
  decides whether execution happens through sync or async SQLAlchemy sessions.
- Shared integration and ORM metadata caches are validated for free-threaded
  execution.
- Dedicated async, free-threaded, and security suites are documented in
  [Testing](testing.md).
