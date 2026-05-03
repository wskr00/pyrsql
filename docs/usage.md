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

## Sort Query

```python
from pyrsql import Sort

sort = Sort.parse("name,asc;company.name,desc")
```

## Pagination

```python
from pyrsql import PageRequest

page = PageRequest.of(0, 25)
```

## SQLAlchemy

```python
from sqlalchemy import select

from pyrsql import Query, Sort, PageRequest
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

## FastAPI Adapter

The FastAPI adapter extracts request parameters and returns a `RequestCriteria`
object that can later be applied to any configured ORM.

Basic usage with the dependency factory:

```python
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select

from pyrsql.adapters.fastapi import criteria_dependency
from pyrsql.orms.sqlalchemy import SQLAlchemyORM

router = APIRouter()
orm = SQLAlchemyORM()
criteria_dep = criteria_dependency()

@router.get("/users")
def list_users(criteria: Annotated[object, Depends(criteria_dep)]):
    stmt = select(User)
    return criteria.apply(stmt, User, orm=orm)
```

The adapter also supports the class-based FastAPI dependency style:

```python
from typing import Annotated

from fastapi import Depends

from pyrsql.adapters.fastapi import CriteriaDependency, FastAPICriteriaConfig

dependency = CriteriaDependency(FastAPICriteriaConfig(default_page_size=25))

async def endpoint(criteria: Annotated[object, Depends(dependency)]):
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
    )
)
```

The adapter translates pyrsql parse and semantic failures into `HTTP 422`
responses using FastAPI `HTTPException`. The error payload includes:

- `parameter`
- `type`
- `message`

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

Current scope:

- compose the FastAPI adapter with `SQLAlchemyORM`
- expose `criteria_dependency()`
- expose `apply(...)`
- expose `select(...)`
- expose `select_dependency(...)`
- expose `count_select(...)`
- expose `count_select_dependency(...)`
- expose `paginated_select(...)`
- expose `paginated_select_dependency(...)`

Out of scope:

- executing queries automatically
- serializing responses
- repository abstractions
- export and summarization helpers

For pagination flows, the integration helper can also build a count query that
preserves filter semantics while ignoring sort and page:

```python
count_stmt = integration.count_select(User, criteria)
```

And the dependency form:

```python
@router.get("/users/count")
def count_users(
    stmt = Depends(integration.count_select_dependency(User)),
):
    return session.execute(stmt).scalar_one()
```

If you want both statements together, use the paginated bundle:

```python
bundle = integration.paginated_select(User, criteria)

items = session.execute(bundle.statement).all()
total = session.execute(bundle.count_statement).scalar_one()
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

Example:

```python
from pyrsql import QueryOptions
from pyrsql.core.json.options import JSONOptions

query = Query.parse(
    "payload.created_at=gt=2026-05-02T10:30:00",
    options=QueryOptions(
        json_options=JSONOptions(
            use_datetime=True,
            path_exists_function="jsonb_path_exists",
            path_exists_tz_function="jsonb_path_exists_tz",
        ),
    ),
)
```

When `use_datetime=True`:

- ISO date/time strings use PostgreSQL `datetime()` jsonpath semantics
- timezone-aware values use `jsonb_path_exists_tz`

Examples:

```python
Query.parse("payload.roles.id==1")
Query.parse("payload.active==true")
Query.parse("payload.score=bt=(10,20)")
Query.parse("payload.tags=='[1,2]'")
Query.parse("payload.meta=='{\"id\":1}'")
```

Current limitations:

- framework adapters
- non-SQLAlchemy ORMs for JSON compilation

## Selector Functions

Filter selectors support functions:

```python
Query.parse(
    "@upper[name]==DEMO",
    options=QueryOptions(procedure_whitelist=("upper",)),
)
```

Sort selectors support functions:

```python
Sort.parse(
    "@upper[name],asc",
    options=SortOptions(procedure_whitelist=("upper",)),
)
```

Nested selectors are supported:

```python
Query.parse(
    "@concat[@upper[code]|#123]==ABC123",
    options=QueryOptions(procedure_whitelist=("upper", "concat")),
)
```

## Literal Selectors

Supported selector literals include:

- `#123`
- `#true`
- `#false`
- `#null`
- `##text`

Example:

```python
Sort.parse(
    "@concat[name|##-suffix],asc",
    options=SortOptions(procedure_whitelist=("concat",)),
)
```

## Options

`QueryOptions` supports:

- `strict_equality`
- `distinct`
- `like_escape_character`
- `field_mapping`
- `model_field_mapping`
- `join_hints`
- `field_whitelist`
- `field_blacklist`
- `model_field_whitelist`
- `model_field_blacklist`
- `procedure_whitelist`
- `procedure_blacklist`
- `operator_registry`
- `custom_predicates`
- `value_converter_registry`
- `field_value_converters`
- `model_field_value_converters`
- `parse_limits`

`SortOptions` supports:

- `field_mapping`
- `model_field_mapping`
- `join_hints`
- `field_whitelist`
- `field_blacklist`
- `model_field_whitelist`
- `model_field_blacklist`
- `procedure_whitelist`
- `procedure_blacklist`
- `sort_limits`

## Distinct

```python
from pyrsql import QueryOptions

query = Query.parse(
    "company.name==acme",
    options=QueryOptions(distinct=True),
)
```

## Join Hints

```python
from pyrsql import QueryOptions
from pyrsql.core.joins import JoinHint

query = Query.parse(
    "company.name==acme",
    options=QueryOptions(
        join_hints={"User.company": JoinHint.LEFT},
    ),
)
```

Current SQLAlchemy support:

- `JoinHint.INNER`
- `JoinHint.LEFT`

`JoinHint.RIGHT` is not supported by the current SQLAlchemy orm.

## Field Mapping

Global field mapping:

```python
Query.parse(
    "companyName==acme",
    options=QueryOptions(
        field_mapping={"companyName": "company.name"},
    ),
)
```

Model-specific field mapping:

```python
Query.parse(
    "company.companyName==acme",
    options=QueryOptions(
        model_field_mapping={
            Company: {"companyName": "name"},
        },
    ),
)
```

## Field Access Control

Global whitelist:

```python
Query.parse(
    "name==demo",
    options=QueryOptions(
        field_whitelist=frozenset({"name"}),
    ),
)
```

Model-specific whitelist:

```python
Query.parse(
    "company.name==acme",
    options=QueryOptions(
        model_field_whitelist={
            Company: frozenset({"id", "name"}),
        },
    ),
)
```

## Value Conversion

The default converter registry supports:

- `str`
- `bool`
- `int`
- `float`
- `Decimal`
- `UUID`
- `date`
- `time`
- `datetime`
- `Enum`
- fallback constructor conversion

`datetime` also supports a date-only fallback:

- `"2026-05-02"` -> `datetime(2026, 5, 2, 0, 0)`

Custom type converter:

```python
from pyrsql import QueryOptions, ValueConverterRegistry
from pyrsql.core.conversion import DEFAULT_VALUE_CONVERTER_REGISTRY

registry = DEFAULT_VALUE_CONVERTER_REGISTRY.with_converter(
    MyType,
    MyType.parse,
)

query = Query.parse(
    "status==active",
    options=QueryOptions(value_converter_registry=registry),
)
```

Field-specific converter:

```python
query = Query.parse(
    "created_at==02/05/2026",
    options=QueryOptions(
        field_value_converters={
            "created_at": lambda raw: datetime.strptime(raw, "%d/%m/%Y"),
        },
    ),
)
```

Model-specific field converter:

```python
query = Query.parse(
    "company.name==demo",
    options=QueryOptions(
        model_field_value_converters={
            Company: {"name": lambda raw: raw.upper()},
        },
    ),
)
```

## Custom Predicates

Custom predicates have two parts:

1. core definition in `QueryOptions`
2. ORM implementation in the ORM instance

```python
from pyrsql import QueryOptions, CustomPredicateDefinition
from pyrsql.parsing.operators import ComparisonOperator

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
```

For SQLAlchemy:

```python
from sqlalchemy import func
from pyrsql.orms.sqlalchemy import SQLAlchemyORM

orm = SQLAlchemyORM(
    custom_predicates={
        "all_match": lambda payload: func.lower(payload.expression)
        == str(payload.values[0]).lower()
    }
)
```
