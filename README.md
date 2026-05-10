# pyrsql

A compiler-oriented RSQL query engine for safe, typed, and extensible
filtering, sorting, and pagination in Python APIs.

[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue?logo=python)](https://pypi.org/project/pyrsql/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

pyrsql compiles RSQL query strings into ORM-specific statement objects
through a language frontend, semantic binder, logical IR, and pluggable
backend lowering - making it easy to expose complex query capabilities in
your API without coupling to a specific ORM or framework.

**Current backends:** SQLAlchemy 2.0  
**Current framework adapters:** FastAPI  
**Planned:** Django ORM, SQLModel, Flask

## Why pyrsql?

Most API filtering libraries are tightly coupled to one ORM or one framework.
pyrsql is built as a **compiler pipeline** - parsing, semantic analysis, and
IR lowering are separate stages. Adding a new ORM backend means implementing
one interface (`ORM`), not rewriting the parser or query language.

- **ORM-neutral core** - `Query`, `Sort`, `PageRequest` have zero ORM dependencies
- **Pluggable backends** - implement `compile_query` / `compile_sort` /
  `compile_page_request` for any ORM
- **Pluggable framework adapters** - FastAPI today, Flask/Django tomorrow
- **Custom operators** - define your own RSQL operators with per-ORM lowering
- **Field policies** - whitelist, blacklist, aliases at global and per-model level
- **Type-safe** - strict mypy, Google-style docstrings, immutable value objects

## Quickstart

```bash
pip install pyrsql[sqlalchemy]
```

```python
import pyrsql
from sqlalchemy import select
from pyrsql.orms.sqlalchemy import SQLAlchemyORM

orm = SQLAlchemyORM()
stmt = select(User)

# Filter: name equals "demo", company name contains "acme"
stmt = pyrsql.parse("name==demo;company.name==acme*").apply(stmt, User, orm=orm)

# Sort: by name ascending, then company name descending
stmt = pyrsql.Sort.parse("name,asc;company.name,desc").apply(stmt, User, orm=orm)

# Paginate: page 0, 25 items per page
stmt = pyrsql.PageRequest.of(0, 25).apply(stmt, User, orm=orm)
```

## Features

### Query (filter)

- 20+ built-in operators: `==`, `!=`, `=gt=`, `=ge=`, `=lt=`, `=le=`, `=in=`, `=out=`, `=like=`, `=ilike=`, `=bt=`, `=na=`, `=nn=`, etc.
- Logical composition: `;` (AND), `,` (OR)
- Grouping with parentheses
- Wildcard matching (`*demo*`) and case-insensitive markers (`^demo`)
- Strict equality mode (literal `*` and `^`)
- Configurable `LIKE` escape character
- `SELECT DISTINCT` support
- Configurable parser limits (query length, depth, argument count)

### Sort

- Multi-field: `name,asc;company.name,desc,ic`
- Ignore-case modifier (`ic`)
- Function selectors: `@upper[name],asc`

### Pagination

- Page-number + page-size API: `PageRequest.of(0, 25)`
- Offset + limit API: `PageRequest.from_offset(offset=50, limit=25)`
- Configurable max page size

### Field Mapping & Access Control

- Aliases: `field_mapping={"username": "user.name"}`
- Whitelist/blacklist: `field_whitelist`, `field_blacklist`
- Per-model policies: `model_field_mapping`, `model_field_whitelist`, `model_field_blacklist`

### Custom Predicates

Define custom operators with ORM-specific lowering:

```python
from pyrsql import CustomPredicateDefinition, QueryOptions
from pyrsql.parsing.operators import ComparisonOperator

all_match = ComparisonOperator(name="all_match", spellings=("=all=",), ...)
options = QueryOptions(
    custom_predicates={
        "all_match": CustomPredicateDefinition(operator=all_match, argument_type=str),
    },
)
```

### Value Conversion

- Built-in: `bool`, `int`, `float`, `Decimal`, `UUID`, `date`, `time`, `datetime`, `enum`
- Custom converters: `ValueConverterRegistry` + `with_converter`
- Field-scoped: `field_value_converters={"created_at": my_converter}`
- Model-scoped: `model_field_value_converters={MyModel: {"field": my_converter}}`

### Join Hints

```python
from pyrsql import QueryOptions
from pyrsql.core.joins import JoinHint

options = QueryOptions(join_hints={"User.company": JoinHint.LEFT})
```

### PostgreSQL JSON / JSONB

- **Whole-document**: direct `==`, `!=`, `=in=`, `=out=`, `=na=`, `=nn=` against JSONB columns
- **Nested path**: `jsonb_path_exists` via PostgreSQL `jsonpath`
- **Structured values**: arrays and objects passed as `jsonpath` vars
- **Temporal**: `JSONOptions(use_datetime=True)` for datetime-aware `jsonpath`
- **JSON sort**: text, integer, float, numeric, boolean, date, time, datetime
- **Custom function names**: `JSONOptions(path_exists_function=...)`

### FastAPI Integration

```python
from fastapi import Depends, FastAPI
from pyrsql.adapters.fastapi import criteria_dependency

app = FastAPI()
dependency = criteria_dependency()

@app.get("/items")
def list_items(criteria = Depends(dependency)):
    ...
```

- Auto-extracts `filter`, `sort`, `page`, `size` from query params
- `HTTP 422` with structured diagnostics on parse/semantic errors
- OpenAPI examples from configuration
- One-based paging support
- Custom query parameter names

### FastAPI + SQLAlchemy Integration

```python
from pyrsql.integrations.fastapi import FastAPISQLAlchemyIntegration

integration = FastAPISQLAlchemyIntegration()

@app.get("/users")
def list_users(stmt = Depends(integration.select_dependency(User))):
    return {"sql": str(stmt)}
```

- `select_dependency`, `count_select_dependency`, `paginated_select_dependency`
- Declarative `resource()` with auto-generated OpenAPI examples
- `applier_dependency` for custom base statements

## Documentation

Full documentation at **[wskr00.github.io/pyrsql](https://wskr00.github.io/pyrsql/)**.

| Section | Description |
|---------|-------------|
| [Quickstart](https://wskr00.github.io/pyrsql/quickstart/) | One-minute primer |
| [Usage](https://wskr00.github.io/pyrsql/usage/query/) | Filter, sort, page, JSON, FastAPI, custom predicates |
| [API Reference](https://wskr00.github.io/pyrsql/reference/api/) | Auto-generated from docstrings |
| [Operators](https://wskr00.github.io/pyrsql/reference/operators/) | Complete operator table |
| [Options](https://wskr00.github.io/pyrsql/reference/options/) | QueryOptions, SortOptions, JSONOptions |
| [Architecture](https://wskr00.github.io/pyrsql/explanation/architecture/) | Pipeline, modules, design |
| [Extensibility](https://wskr00.github.io/pyrsql/explanation/extensibility/) | Adding backends and adapters |
| [Contributing](https://wskr00.github.io/pyrsql/contributing/) | Setup, workflow, standards |

## Development Principles

- Object-oriented design
- SOLID principles
- Google Python Style Guide
- Strong typing
- ORM-neutral public API

## License

[MIT](LICENSE).
