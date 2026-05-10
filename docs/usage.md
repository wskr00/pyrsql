# pyrsql Usage Guide

- [Installation](#installation)
- [Core Concepts](#core-concepts)
- [Filter Queries](#filter-queries)
- [Sort](#sort)
- [Pagination](#pagination)
- [Field Mapping & Access Control](#field-mapping--access-control)
- [Custom Predicates](#custom-predicates)
- [Value Conversion](#value-conversion)
- [Join Hints](#join-hints)
- [JSON / JSONB](#json--jsonb)
- [FastAPI Adapter](#fastapi-adapter)
- [FastAPI + SQLAlchemy Integration](#fastapi--sqlalchemy-integration)

## Installation

```bash
pip install pyrsql                    # core only
pip install pyrsql[sqlalchemy]        # with SQLAlchemy
pip install pyrsql[fastapi]           # with FastAPI
pip install pyrsql[fastapi,sqlalchemy]  # both
```

## Core Concepts

pyrsql compiles RSQL query strings into ORM-specific statement objects.
The pipeline is:

```text
RSQL string → parsing → AST → semantic binding → logical IR → ORM lowering → ORM statement
```

Three package-level helpers are available:

```python
import pyrsql

query = pyrsql.parse("name==demo")                     # parse only
result = pyrsql.compile("name==demo", orm=my_orm)       # parse + compile
applied = pyrsql.apply(target, Model, "name==demo", orm=my_orm)  # full cycle
```

Or use the object-oriented API directly:

```python
from pyrsql import Query, Sort, PageRequest

query = Query.parse("name==demo")
sort = Sort.parse("name,asc")
page = PageRequest.of(0, 25)
```

## Filter Queries

### Basic comparisons

```python
Query.parse("name==demo")          # equal
Query.parse("name!=demo")          # not equal
Query.parse("age=gt=18")           # greater than
Query.parse("age=ge=18")           # greater or equal
Query.parse("age=lt=65")           # less than
Query.parse("age=le=65")           # less or equal
Query.parse("age>18")              # greater than (symbol)
Query.parse("age>=18")             # greater or equal (symbol)
Query.parse("age<65")              # less than (symbol)
Query.parse("age<=65")             # less or equal (symbol)
```

### Membership and null checks

```python
Query.parse("id=in=(1,2,3)")       # IN
Query.parse("id=out=(4,5)")        # NOT IN
Query.parse("name=na=")            # IS NULL
Query.parse("name=nn=")            # IS NOT NULL
```

### Text matching

```python
Query.parse("name=like=demo*")     # LIKE
Query.parse("name=notlike=demo")   # NOT LIKE
Query.parse("name=ic=demo*")       # ILIKE (case-insensitive)
Query.parse("name=ilike=DEMO")     # ILIKE alias
```

### Range

```python
Query.parse("score=bt=(10,20)")    # BETWEEN 10 AND 20
Query.parse("score=nb=(10,20)")    # NOT BETWEEN
```

### Logical composition

```python
Query.parse("name==demo;age=gt=18")       # AND (semicolon)
Query.parse("name==demo,age=gt=18")       # OR (comma)
Query.parse("(name==demo;age=gt=18),status==active")  # grouping
```

### Wildcard matching in equality

By default, `*` in equality expressions is treated as a `LIKE` wildcard:

```python
Query.parse("name==*demo*")        # becomes LIKE '%demo%'
```

Disable with strict mode:

```python
Query.parse("name=='*demo*'", options=QueryOptions(strict_equality=True))
```

### Case-insensitive equality marker

Prefix the value with `^` for case-insensitive equality:

```python
Query.parse("name==^demo")         # case-insensitive via LOWER()
```

### LIKE escape character

```python
Query.parse("name=like='$%'", options=QueryOptions(like_escape_character="$"))
```

### DISTINCT

```python
Query.parse("company.name==demo", options=QueryOptions(distinct=True))
```

### Function selectors

Whitelist SQL functions to use in filter expressions:

```python
Query.parse(
    "@upper[name]==DEMO",
    options=QueryOptions(procedure_whitelist=("upper",)),
)
```

### Parser limits

```python
from pyrsql.parsing.limits import ParseLimits

Query.parse("...", options=QueryOptions(
    parse_limits=ParseLimits(
        max_query_length=4096,
        max_expression_depth=8,
        max_node_count=512,
    ),
))
```

## Sort

### Basic sort

```python
Sort.parse("name")                 # ascending (default)
Sort.parse("name,asc")             # explicit ascending
Sort.parse("name,desc")            # descending
```

### Multi-field

```python
Sort.parse("name,asc;company.name,desc")
```

### Ignore case

```python
Sort.parse("name,desc,ic")         # case-insensitive descending
```

### Function selectors

```python
Sort.parse(
    "@upper[name],asc",
    options=SortOptions(procedure_whitelist=("upper",)),
)
```

### Sort limits

```python
from pyrsql.sorting.limits import SortLimits

Sort.parse("...", options=SortOptions(
    sort_limits=SortLimits(max_fields=5, max_sort_length=256),
))
```

## Pagination

### Page-number based

```python
page = PageRequest.of(2, 25)       # page 2, 25 items/page → offset 50
page = PageRequest.of(0, 10)       # first page
```

### Offset based

```python
page = PageRequest.from_offset(offset=20, limit=10)  # page 2, 10 items/page
```

### Applying to a statement

```python
stmt = page.apply(stmt, User, orm=orm)
```

## Field Mapping & Access Control

### Global field aliases

```python
options = QueryOptions(field_mapping={"username": "user.name"})
query = Query.parse("username==demo", options=options)
```

### Global whitelist / blacklist

```python
options = QueryOptions(
    field_whitelist=frozenset({"name", "email"}),
    field_blacklist=frozenset({"password"}),
)
```

### Per-model policies

```python
options = QueryOptions(
    model_field_mapping={User: {"companyName": "name"}},
    model_field_whitelist={User: frozenset({"name", "email"})},
    model_field_blacklist={Admin: frozenset({"internal_notes"})},
)
```

### Procedure (function) policies

Procedure whitelist/blacklist use regex patterns:

```python
options = QueryOptions(
    procedure_whitelist=("upper", "concat|lower"),
    procedure_blacklist=("dangerous_.*",),
)
```

## Custom Predicates

Define custom operators with ORM-specific lowering:

```python
from pyrsql import CustomPredicateDefinition, QueryOptions
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
query = Query.parse("name=all=demo", options=options)
```

For SQLAlchemy, register an ORM-specific lowering function:

```python
from pyrsql.orms.sqlalchemy import SQLAlchemyORM
from sqlalchemy import func

orm = SQLAlchemyORM(
    custom_predicates={
        "all_match": lambda payload: (
            func.lower(payload.expression) == str(payload.values[0]).lower()
        ),
    },
)
```

## Value Conversion

### Built-in type converters

`bool`, `int`, `float`, `Decimal`, `UUID`, `date`, `time`, `datetime`,
enum members (by name or value), and `dict`/`list` from JSON strings.

### Custom converter registration

```python
from pyrsql import ValueConverterRegistry

registry = ValueConverterRegistry({}).with_converter(str, lambda raw: raw.upper())
```

### Field-scoped converters

```python
options = QueryOptions(
    field_value_converters={
        "created_at": lambda raw: datetime.strptime(raw, "%d/%m/%Y"),
    },
)
```

### Model-scoped converters

```python
options = QueryOptions(
    model_field_value_converters={
        User: {"status": lambda raw: Status[raw.upper()]},
    },
)
```

### Custom converter registry

```python
options = QueryOptions(
    value_converter_registry=ValueConverterRegistry({str: my_converter}),
)
```

## Join Hints

Control how relationships are joined:

```python
from pyrsql import QueryOptions
from pyrsql.core.joins import JoinHint

options = QueryOptions(join_hints={"User.company": JoinHint.LEFT})
```

Supported hints: `JoinHint.INNER`, `JoinHint.LEFT`, `JoinHint.RIGHT`.

`RIGHT` joins are rejected by the SQLAlchemy backend.

## JSON / JSONB

PostgreSQL JSON and JSONB columns are supported via two distinct query modes.

### Whole-document comparison

When the selector targets the JSON column directly, values are compared as
JSONB:

```python
Query.parse('payload=={"kind":"demo"}')     # JSON object equality
Query.parse('payload==["rg","cpf"]')         # JSON array equality
Query.parse("payload=na=")                   # IS NULL
Query.parse("payload=nn=")                   # IS NOT NULL
Query.parse("payload=in=([1,2],[3,4])")     # IN
```

Supported whole-document operators: `==`, `!=`, `=in=`, `=out=`, `=na=`, `=nn=`.

### Nested path comparison

Traversal into the JSON document uses PostgreSQL `jsonpath`:

```python
Query.parse("payload.user.id==1")
Query.parse("payload.user.name==demo")
Query.parse("payload.tags==[1,2]")
```

Arrays and objects are passed through `jsonpath` vars:

```python
Query.parse("payload.tags=='[1,2]'")         # quoted array → vars payload
Query.parse("payload.meta=='{\"id\":1}'")    # quoted object → vars payload
```

### Temporal JSON path semantics

```python
from pyrsql import JSONOptions, QueryOptions

query = Query.parse(
    "payload.created_at=gt=2026-05-01T10:30:00Z",
    options=QueryOptions(json_options=JSONOptions(use_datetime=True)),
)
```

With `use_datetime=True`, datetime values are rendered as `.datetime()` in
the `jsonpath` expression. For timezone-aware values, `jsonb_path_exists_tz`
is used.

### Custom JSON path function names

```python
options = QueryOptions(json_options=JSONOptions(
    path_exists_function="my_custom_json_path_exists",
    path_exists_tz_function="my_custom_json_path_exists_tz",
))
```

### JSON Sort

Nested JSON sort defaults to text semantics:

```python
Sort.parse("payload.user.name,asc")
```

For typed JSON values, configure explicitly:

```python
from pyrsql import JSONOptions, JSONSortScalarType, SortOptions

Sort.parse("payload.user.id,asc", options=SortOptions(json_options=JSONOptions(
    sort_field_types={"payload.user.id": JSONSortScalarType.INTEGER},
)))
```

Supported scalar types: `TEXT`, `INTEGER`, `FLOAT`, `NUMERIC`, `BOOLEAN`,
`DATE`, `TIME`, `DATETIME`, `DATETIME_TZ`.

Whole-document JSON sort requires explicit `TEXT` configuration; other
whole-document sort types are rejected.

## FastAPI Adapter

### Basic usage

```python
from typing import Annotated
from fastapi import Depends, FastAPI
from pyrsql.adapters.fastapi import RequestCriteria, criteria_dependency

app = FastAPI()
dependency = criteria_dependency()

@app.get("/items")
def list_items(criteria: Annotated[RequestCriteria, Depends(dependency)]):
    return {"is_empty": criteria.is_empty}
```

The adapter extracts `filter`, `sort`, `page`, and `size` from query
parameters and builds a `RequestCriteria`.

### Configuration

```python
from pyrsql.adapters.fastapi import FastAPICriteriaConfig

config = FastAPICriteriaConfig(
    filter_parameter="where",        # custom query param names
    sort_parameter="order",
    page_parameter="p",
    size_parameter="per_page",
    default_page_size=25,
    max_page_size=100,
    one_based_paging=True,           # page numbers start at 1
    query_options=QueryOptions(strict_equality=True),
)
dependency = criteria_dependency(config)
```

### Class-based dependency

```python
from pyrsql.adapters.fastapi import CriteriaDependency

dependency = CriteriaDependency(FastAPICriteriaConfig(default_page_size=15))

@app.get("/items")
def list_items(criteria: Annotated[RequestCriteria, Depends(dependency)]):
    ...
```

### OpenAPI examples

```python
config = FastAPICriteriaConfig(
    filter_openapi_examples={
        "by_name": {"summary": "Filter by name", "value": "name==demo"},
    },
    sort_openapi_examples={
        "newest": {"summary": "Newest first", "value": "created_at,desc"},
    },
)
```

### Error handling

When parsing or semantic binding fails, the adapter raises `HTTPException(422)`
with a structured payload:

```json
{
  "detail": {
    "parameter": "filter",
    "type": "query_parse_error",
    "errors": [
      {
        "code": "parse_error",
        "message": "...",
        "location": {"index": 4, "line": 1, "column": 5}
      }
    ]
  }
}
```

Error types: `query_parse_error`, `query_semantic_error`, `sort_parse_error`,
`sort_semantic_error`, page validation errors.

## FastAPI + SQLAlchemy Integration

### Setup

```python
from pyrsql.integrations.fastapi import FastAPISQLAlchemyIntegration

integration = FastAPISQLAlchemyIntegration()
```

### Dependency factories

```python
@app.get("/users")
def list_users(
    stmt: Annotated[Any, Depends(integration.select_dependency(User))],
):
    return {"sql": str(stmt.compile(compile_kwargs={"literal_binds": True}))}

@app.get("/users/count")
def count_users(
    stmt: Annotated[Any, Depends(integration.count_select_dependency(User))],
):
    ...

@app.get("/users/paginated")
def paginated_users(
    bundle: Annotated[Any, Depends(integration.paginated_select_dependency(User))],
):
    # bundle.statement → the filtered + sorted + paged SELECT
    # bundle.count_statement → the filtered count SELECT
    ...
```

### Declarative resources

```python
users = integration.resource(
    User,
    filterable_fields={"id", "name"},
    sortable_fields={"name"},
    default_sort="name,desc",
    max_page_size=50,
    filter_examples={"by_name": {"summary": "By name", "value": "name==demo"}},
)

@app.get("/users")
def list_users(stmt: Annotated[Any, Depends(users.select_dependency())]):
    ...
```

Resources auto-generate OpenAPI examples for filterable and sortable fields.

### Custom base statement

```python
users = integration.resource(
    User,
    statement_factory=lambda: select(User).where(User.status == "active"),
    default_sort="-name",
)
```

### Applying criteria directly

```python
stmt = integration.apply(select(User), User, request_criteria)
stmt = integration.select(User, request_criteria)
stmt = integration.count_select(User, request_criteria)
bundle = integration.paginated_select(User, request_criteria)
```

### Custom ORM configuration

```python
from pyrsql.adapters.fastapi import FastAPICriteriaConfig

integration = FastAPISQLAlchemyIntegration(
    orm=SQLAlchemyORM(...),
    criteria_config=FastAPICriteriaConfig(default_page_size=20),
)
```
