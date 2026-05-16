# Quickstart

## Install

```bash
pip install pyrsql                    # core only
pip install pyrsql[sqlalchemy]        # with SQLAlchemy
pip install pyrsql[fastapi]           # with FastAPI
pip install pyrsql[fastapi,sqlalchemy]  # both
```

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
Parse and semantic errors become `HTTP 422` with structured diagnostics.

## FastAPI + SQLAlchemy

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

- Shared integration and ORM metadata caches are validated for free-threaded
  execution.
- Dedicated async, free-threaded, and security suites are documented in
  [Testing](testing.md).
