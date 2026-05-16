# FastAPI + SQLAlchemy

## Setup

```python
from pyrsql.integrations.fastapi import FastAPISQLAlchemyIntegration

integration = FastAPISQLAlchemyIntegration()
```

The integration composes:

- the FastAPI adapter, which parses `filter`, `sort`, `page`, and `size`
- the SQLAlchemy backend, which lowers compiled criteria into `Select`
  statements

It does not execute database I/O. It only builds SQLAlchemy statements.

## Route-ready dependencies

```python
from typing import Annotated, Any

from fastapi import Depends, FastAPI

app = FastAPI()

@app.get("/users")
def list_users(
    stmt: Annotated[Any, Depends(integration.select_dependency(User))],
):
    return {"sql": str(stmt)}

@app.get("/users/count")
def count_users(
    stmt: Annotated[Any, Depends(integration.count_select_dependency(User))],
):
    ...

@app.get("/users/paginated")
def paginated_users(
    bundle: Annotated[
        Any,
        Depends(integration.paginated_select_dependency(User)),
    ],
):
    # bundle.statement -> filtered + sorted + paged SELECT
    # bundle.count_statement -> filtered count SELECT
    ...
```

`paginated_select_dependency(...)` returns a
`SQLAlchemyPaginatedSelect` bundle with:

- `statement`
- `count_statement`

## Declarative resources

```python
users = integration.resource(
    User,
    filterable_fields={"id", "name"},
    sortable_fields={"name"},
    default_sort="name,desc",
    max_page_size=50,
    filter_examples={
        "by_name": {"summary": "By name", "value": "name==demo"},
    },
)

@app.get("/users")
def list_users(
    stmt: Annotated[Any, Depends(users.select_dependency())],
):
    ...
```

Resources are useful when one model/route pair has a stable public contract:

- allowed filter fields
- allowed sort fields
- default sort
- OpenAPI examples
- page-size limits

Also available:

- `users.count_select_dependency()`
- `users.paginated_select_dependency()`
- `users.applier_dependency()`

## Custom base statement

```python
from sqlalchemy import select

users = integration.resource(
    User,
    statement_factory=lambda: select(User).where(User.status == "active"),
    default_sort="-name",
)
```

Use `statement_factory` when the public route should always start from one
restricted base query.

## Applying criteria directly

```python
stmt = integration.apply(select(User), User, request_criteria)
stmt = integration.select(User, request_criteria)
stmt = integration.count_select(User, request_criteria)
bundle = integration.paginated_select(User, request_criteria)
```

These helpers are useful outside route dependencies, for example in service
layers or tests.

## Error behavior

Adapter-layer failures still return the structured FastAPI `422` payloads from
the request adapter.

Backend-layer failures are also normalized to `422` in the integration layer.
Examples:

- filtering on an unmapped field
- sorting on an unmapped field
- backend-specific lowering errors

This avoids leaking raw SQLAlchemy exceptions as `500` responses.

## Free-threaded behavior

The integration caches dependency callables and base `select(model)` statements
per model. Those shared caches are protected explicitly for free-threaded
execution.

## Async note

This page shows the synchronous route shape. The integration is also compatible
with `async def` routes and `AsyncSession`; see [Async Flows](async.md).
