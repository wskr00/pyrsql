# Extensibility

pyrsql is designed to support multiple ORM backends and framework adapters.
The core (`pyrsql.core`, `pyrsql.ir`, `pyrsql.parsing`, `pyrsql.semantic`)
has zero dependencies on any ORM or framework.

## Adding a new ORM backend

Implement the `ORM` abstract base class:

```python
from pyrsql.orms.base import ORM, CompiledQuery, CompiledSort, CompiledPageRequest

class MyORM(ORM):
    @property
    def name(self) -> str:
        return "my-orm"

    def compile_query(self, query: Query) -> CompiledQuery:
        # Return a compiled object that can apply the query to a target
        ...

    def compile_sort(self, sort: Sort) -> CompiledSort:
        ...

    def compile_page_request(self, page_request: PageRequest) -> CompiledPageRequest:
        ...
```

Each `compile_*` method receives the ORM-neutral IR and returns a compiled
object with an `apply(target, model)` method.

The current reference implementation is `SQLAlchemyORM` in
`pyrsql.orms.sqlalchemy`.

## Adding a new framework adapter

Create a module under `pyrsql.adapters` that:

1. Extracts RSQL parameters from HTTP requests
2. Builds `RequestCriteria` (query, sort, page)
3. Translates parse/semantic errors into framework-appropriate error responses

The FastAPI adapter (`pyrsql.adapters.fastapi`) is the reference:
`FastAPICriteriaConfig` holds parameter names and defaults;
`criteria_dependency()` returns a FastAPI dependency callable.

## Backend contract in detail

### CompiledQuery

```python
class CompiledQuery(Protocol):
    def apply(self, target: _TargetT, model: type[_ModelT]) -> _TargetT: ...
```

Receives an ORM-specific target (e.g., a SQLAlchemy `Select`) and the
model class, returns the modified target with query conditions applied.

### CompiledSort

Same contract as `CompiledQuery` - applies sort ordering to the target.

### CompiledPageRequest

Same contract - applies `LIMIT`/`OFFSET` to the target.

## Planned backends

- **Django ORM** - compile to Django `QuerySet` with `.filter()`, `.order_by()`
- **SQLModel** - thin wrapper over SQLAlchemy, mostly reuse `SQLAlchemyORM`
- **Flask** - adapter for extracting parameters from Flask `request.args`
