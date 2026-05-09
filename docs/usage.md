# pyrsql Usage

## Installation

Core only:

```bash
pip install pyrsql
```

With SQLAlchemy support:

```bash
pip install pyrsql[sqlalchemy]
```

With FastAPI support:

```bash
pip install pyrsql[fastapi]
```

With FastAPI and SQLAlchemy support:

```bash
pip install pyrsql[fastapi,sqlalchemy]
```

## Core Objects

The main public objects are:

- `Query`
- `Sort`
- `PageRequest`
- `QueryOptions`
- `SortOptions`

The package-level helpers are:

- `pyrsql.parse(...)`
- `pyrsql.compile(...)`
- `pyrsql.apply(...)`

## Filter Query

```python
from pyrsql import Query

query = Query.parse("name==demo;company.name==acme")
```

Package-level helper:

```python
import pyrsql

query = pyrsql.parse("name==demo")
```

`Query.parse(...)` returns a `Query` carrying:

- `text`
- `expression`
- `bound_expression`

`bound_expression` is the logical IR consumed by ORM backends.

## Sort Query

```python
from pyrsql import Sort

sort = Sort.parse("name,asc;company.name,desc")
```

`Sort.parse(...)` returns a `Sort` carrying:

- `text`
- `fields`
- `bound_sort`

## Pagination

```python
from pyrsql import PageRequest

page = PageRequest.of(0, 25)
```

`PageRequest` also exposes `bound_page`.

## SQLAlchemy

```python
from sqlalchemy import select

from pyrsql import PageRequest, Query, Sort
from pyrsql.orms.sqlalchemy import SQLAlchemyORM

orm = SQLAlchemyORM()

stmt = select(User)
stmt = Query.parse("company.name==acme").apply(
    stmt,
    User,
    orm=orm,
)
stmt = Sort.parse("name,asc").apply(
    stmt,
    User,
    orm=orm,
)
stmt = PageRequest.of(0, 20).apply(
    stmt,
    User,
    orm=orm,
)
```

## JSON / JSONB

PostgreSQL JSON and JSONB fields support two distinct query modes.

### Whole-document comparison

When the selector targets the JSON column itself, pyrsql uses direct JSONB
comparison semantics instead of forcing everything through `jsonpath`.

Examples:

```python
from pyrsql import Query

Query.parse('payload=={"kind":"demo"}')
Query.parse('payload==["rg","cpf"]')
Query.parse("payload=nn=")
```

Supported whole-document operators:

- `==`
- `!=`
- `=in=`
- `=out=`
- `=na=`
- `=nn=`

### Nested path comparison

When the selector traverses inside the JSON document, pyrsql uses PostgreSQL
`jsonpath` lowering.

Examples:

```python
from pyrsql import Query

Query.parse("payload.user.id==1")
Query.parse("payload.user.name==demo")
Query.parse("payload.tags==[1,2]")
```

For structured values like arrays and objects, pyrsql passes values through
PostgreSQL `jsonpath` vars instead of inlining invalid literals into the
`jsonpath` expression.

### Temporal JSON path semantics

You can enable datetime-aware JSON comparisons with `JSONOptions`.

```python
from pyrsql.core import JSONOptions, QueryOptions
from pyrsql import Query

query = Query.parse(
    "payload.created_at=ge=2026-05-01T10:30:00+00:00",
    options=QueryOptions(
        json_options=JSONOptions(use_datetime=True),
    ),
)
```

## JSON Sort

By default, nested JSON sort expressions use text semantics.

```python
from pyrsql import Sort

sort = Sort.parse("payload.user.name,asc")
```

For numeric, boolean, or temporal JSON values, configure the sort type
explicitly with `JSONOptions.sort_field_types`.

```python
from pyrsql import Sort
from pyrsql.core import JSONOptions, JSONSortScalarType, SortOptions

sort = Sort.parse(
    "payload.user.id,asc",
    options=SortOptions(
        json_options=JSONOptions(
            sort_field_types={
                "payload.user.id": JSONSortScalarType.INTEGER,
            }
        )
    ),
)
```

Supported JSON sort scalar types:

- `TEXT`
- `INTEGER`
- `FLOAT`
- `NUMERIC`
- `BOOLEAN`
- `DATE`
- `TIME`
- `DATETIME`
- `DATETIME_TZ`

### Whole-document JSON sort

Whole-document JSON sort is intentionally restricted.

- without explicit configuration: pyrsql rejects it
- with explicit `TEXT` configuration: pyrsql allows it
- non-text whole-document sort semantics are rejected

Example:

```python
from pyrsql import Sort
from pyrsql.core import JSONOptions, JSONSortScalarType, SortOptions

sort = Sort.parse(
    "payload,asc",
    options=SortOptions(
        json_options=JSONOptions(
            sort_field_types={
                "payload": JSONSortScalarType.TEXT,
            }
        )
    ),
)
```

## FastAPI Adapter

The FastAPI adapter extracts request parameters and returns a `RequestCriteria`
object that can later be applied to any configured ORM.

Basic usage with the dependency factory:

```python
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select

from pyrsql.adapters.fastapi import RequestCriteria, criteria_dependency
from pyrsql.orms.sqlalchemy import SQLAlchemyORM

router = APIRouter()
orm = SQLAlchemyORM()
criteria_dep = criteria_dependency()

@router.get("/users")
def list_users(
    criteria: Annotated[RequestCriteria, Depends(criteria_dep)],
):
    stmt = select(User)
    return criteria.apply(stmt, User, orm=orm)
```

The adapter also supports the class-based FastAPI dependency style:

```python
from typing import Annotated

from fastapi import Depends

from pyrsql.adapters.fastapi import (
    CriteriaDependency,
    FastAPICriteriaConfig,
    RequestCriteria,
)

dependency = CriteriaDependency(FastAPICriteriaConfig(default_page_size=25))

async def endpoint(
    criteria: Annotated[RequestCriteria, Depends(dependency)],
):
    ...
```

Supported query parameters by default:

- `filter`
- `sort`
- `page`
- `size`

Configuration options include:

- custom parameter names
- `default_page_size`
- `max_page_size`
- zero-based or one-based paging
- `QueryOptions`
- `SortOptions`
- OpenAPI examples for `filter`, `sort`, `page`, and `size`

Example:

```python
from pyrsql.adapters.fastapi import FastAPICriteriaConfig, criteria_dependency
from pyrsql.core.options import QueryOptions

criteria_dep = criteria_dependency(
    FastAPICriteriaConfig(
        filter_parameter="where",
        sort_parameter="order",
        page_parameter="p",
        size_parameter="per_page",
        default_page_size=20,
        one_based_paging=True,
        query_options=QueryOptions(strict_equality=True),
        filter_openapi_examples={
            "by_name": {
                "summary": "By name",
                "value": "name==demo",
            }
        },
    )
)
```

The adapter translates pyrsql parse and semantic failures into `HTTP 422`
responses using FastAPI `HTTPException`.

Current error payload shape:

```json
{
  "detail": {
    "parameter": "filter",
    "error_type": "query_semantic_error",
    "message": "Field 'password' is not allowed.",
    "details": [
      {
        "code": "field_not_whitelisted",
        "message": "Field 'password' is not allowed.",
        "field": "password"
      }
    ]
  }
}
```

Top-level payload fields:

- `parameter`
- `error_type`
- `message`
- `details`

Detail item fields:

- `code`
- `message`
- `field`

## FastAPI + SQLAlchemy Integration

If you want less boilerplate for `FastAPI + SQLAlchemy`, use the integration
helper.

```python
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from pyrsql.adapters.fastapi import RequestCriteria
from pyrsql.integrations.fastapi import FastAPISQLAlchemyIntegration

router = APIRouter()
integration = FastAPISQLAlchemyIntegration()

@router.get("/users")
def list_users(
    criteria: Annotated[
        RequestCriteria,
        Depends(integration.criteria_dependency()),
    ],
    session: Session,
):
    stmt = integration.select(User, criteria)
    return session.execute(stmt)
```

You can also depend on a ready-to-use `Select` directly:

```python
from typing import Annotated, Any

from fastapi import Depends

from pyrsql.integrations.fastapi import FastAPISQLAlchemyIntegration

integration = FastAPISQLAlchemyIntegration()

@router.get("/users")
def list_users(
    stmt: Annotated[Any, Depends(integration.select_dependency(User))],
):
    return session.execute(stmt)
```

The integration also exposes:

- `apply(statement, model, criteria)`
- `count_select(model, criteria)`
- `count_select_dependency(model)`
- `paginated_select(model, criteria)`
- `paginated_select_dependency(model)`

For pagination flows:

```python
bundle = integration.paginated_select(User, criteria)

items = session.execute(bundle.statement).all()
total = session.execute(bundle.count_statement).scalar_one()
```

## Declarative FastAPI Resources

For endpoint-oriented FastAPI usage, the preferred API is the declarative
resource layer.

```python
from fastapi import Depends

from pyrsql.integrations.fastapi import FastAPISQLAlchemyIntegration

integration = FastAPISQLAlchemyIntegration()

users = integration.resource(
    User,
    filterable_fields={"id", "name", "company.name"},
    sortable_fields={"name", "created_at"},
    default_sort="-created_at",
    max_page_size=100,
)
```

This resource object exposes:

- `criteria_dependency()`
- `select_dependency()`
- `count_select_dependency()`
- `paginated_select_dependency()`
- `applier_dependency()`
- `select(criteria)`
- `count_select(criteria)`
- `paginated_select(criteria)`
- `applier(criteria)`

### Route-ready `Select`

```python
@router.get("/users")
def list_users(
    stmt = Depends(users.select_dependency()),
):
    return session.execute(stmt)
```

### Apply criteria to an existing statement

Use `applier_dependency()` when the route already has a base statement:

```python
@router.get("/users")
def list_users(
    apply_query = Depends(users.applier_dependency()),
):
    stmt = apply_query(
        select(User).where(User.tenant_id == current_user.tenant_id)
    )
    return session.execute(stmt)
```

This is the correct path for:

- tenant scoping
- soft-delete base filters
- eager loading
- custom `select(...)` shapes

### Statement factory

If many routes share the same base statement, configure it once on the
resource:

```python
users = integration.resource(
    User,
    default_sort="-created_at",
    statement_factory=lambda: (
        select(User).where(User.deleted_at.is_(None))
    ),
)
```

The `statement_factory` contract is:

- it must be callable
- it must return a SQLAlchemy `Select`
- it must return a `Select` compatible with the resource `model`
- it is called per use and should stay cheap and side-effect free

### Automatic OpenAPI examples

The resource layer can publish OpenAPI examples automatically from declarative
configuration:

```python
users = integration.resource(
    User,
    filterable_fields={"id", "name"},
    sortable_fields={"name"},
    default_sort="-name",
)
```

Custom examples can still be provided explicitly:

```python
users = integration.resource(
    User,
    filter_examples={
        "by_name": {
            "summary": "By name",
            "value": "name==demo",
        }
    },
    sort_examples={
        "by_name_desc": {
            "summary": "Newest first",
            "value": "name,desc",
        }
    },
)
```

## JSON / JSONB

The current `SQLAlchemy` ORM supports PostgreSQL-style JSON filtering and
sorting on `JSON` and `JSONB` columns.

Filter by nested JSON path:

```python
Query.parse("payload.user.id==1")
```

Sort by nested JSON path:

```python
Sort.parse("payload.user.id,asc")
```

Current behavior:

- `JSON` columns are cast to `JSONB`
- filter translation uses PostgreSQL JSON path predicates via SQLAlchemy
- sort translation uses PostgreSQL JSON path extraction operators via SQLAlchemy
- arrays can be traversed with dotted paths such as `payload.roles.id==1`

Current scope:

- nested path filters such as `payload.user.id==1`
- string, boolean, numeric, and `null` JSON scalar comparisons
- quoted JSON arrays and objects in filter arguments
- `in`, `out`, `between`, `like`, and ignore-case JSON predicates
- JSON and JSONB column support in the `SQLAlchemy` ORM

## JSON Options

`QueryOptions` and `SortOptions` expose `json_options`.

Current options:

- `path_exists_function`
- `path_exists_tz_function`
- `use_datetime`
