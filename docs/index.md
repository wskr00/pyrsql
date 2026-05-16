# pyrsql

A compiler-oriented RSQL query engine for safe, typed, and extensible
filtering, sorting, and pagination in Python APIs.

pyrsql compiles RSQL query strings into ORM-specific statement objects
through a multi-stage pipeline - making it easy to expose complex query
capabilities in your API without coupling to a specific ORM or framework.

## Install

```bash
pip install pyrsql[sqlalchemy]
```

## First query

```python
import pyrsql
from sqlalchemy import select
from pyrsql.orms.sqlalchemy import SQLAlchemyORM

orm = SQLAlchemyORM()
stmt = pyrsql.parse("name==demo;age=gt=18").apply(select(User), User, orm=orm)
```

## Key features

- **ORM-neutral core** - `Query`, `Sort`, `PageRequest` have zero ORM dependencies
- **Pluggable backends** - SQLAlchemy 2.0 today, Django ORM / SQLModel planned
- **Pluggable adapters** - FastAPI today, Flask planned
- **20+ built-in operators** - `==`, `=like=`, `=in=`, `=bt=`, `=nn=`, etc.
- **Custom operators** - define your own RSQL operators with per-ORM lowering
- **Field policies** - whitelist, blacklist, aliases (global + per-model)
- **JSON / JSONB** - PostgreSQL `jsonpath` with structured values and datetime support
- **Type-safe** - strict mypy, Google-style docstrings, immutable value objects
- **Async-compatible execution** - generated SQLAlchemy statements work with
  both `Session` and `AsyncSession`
- **Security-oriented request handling** - parser/sort limits, structural
  allowlists/blocklists, and sanitized FastAPI error payloads
- **Free-threaded-safe shared caches** - integration and ORM helper caches are
  guarded for concurrent access

## Integration options

- **FastAPI adapter** - parse `filter`, `sort`, `page`, and `size` into
  `RequestCriteria`
- **FastAPI + SQLAlchemy integration** - route-ready dependencies,
  declarative `resource()` helpers, count/paginated bundles, and normalized
  backend `HTTP 422` translation

## Next steps

- [Quickstart](quickstart.md)
- [FastAPI Adapter](usage/fastapi.md)
- [FastAPI + SQLAlchemy](usage/fastapi-sqlalchemy.md)
- [Async Flows](usage/async.md)
- [Architecture](explanation/architecture.md)
