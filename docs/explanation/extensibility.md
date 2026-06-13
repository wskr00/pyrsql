# Extensibility

`pyrsql` is designed to support multiple ORM backends and framework adapters.
The core (`pyrsql.core`, `pyrsql.parsing`, `pyrsql.semantic`,
`pyrsql.sorting`) has zero dependencies on any ORM or framework.

## Adding a new ORM backend

Implement the `ORM` abstract base class:

```python
from pyrsql.orms.base import ORM, CompiledPageRequest, CompiledQuery, CompiledSort

class MyORM(ORM):
    @property
    def name(self) -> str:
        return "my-orm"

    def compile_query(self, query: Query) -> CompiledQuery:
        ...

    def compile_sort(self, sort: Sort) -> CompiledSort:
        ...

    def compile_page_request(self, page_request: PageRequest) -> CompiledPageRequest:
        ...
```

Each `compile_*` method receives one ORM-neutral core object (`Query`, `Sort`,
or `PageRequest`) and returns a compiled object with an `apply(target, model)`
method.

The current reference implementation is `SQLAlchemyORM` in
`pyrsql.orms.sqlalchemy`.

## Adding a new framework adapter

Create a module under `pyrsql.adapters` that:

1. extracts query parameters from requests
2. builds `RequestCriteria`
3. translates parse, semantic, and page-validation failures into
   framework-appropriate error responses

The FastAPI adapter (`pyrsql.adapters.fastapi`) is the reference:

- `FastAPICriteriaConfig` holds public parameter names and defaults
- `criteria_dependency()` returns a FastAPI dependency callable

## Backend contract in detail

### `CompiledQuery`

```python
class CompiledQuery(Protocol):
    def apply(self, target: _TargetT, model: type[_ModelT]) -> _TargetT: ...
```

Receives an ORM-specific target and model class, then returns the modified
target with query conditions applied.

### `CompiledSort`

Same contract as `CompiledQuery`, but applies sort ordering.

### `CompiledPageRequest`

Same contract, but applies pagination semantics such as `LIMIT` and `OFFSET`.

## Integration layer

Adapters and ORMs can stay independent. The `integrations/` package is where
stack-specific DX belongs.

For example, `integrations.fastapi.sqlalchemy` is allowed to know both:

- the FastAPI adapter contract
- the SQLAlchemy backend contract

That is the right place for:

- route-ready dependencies
- paginated statement bundles
- OpenAPI example generation tied to SQLAlchemy model metadata

## Planned backends and adapters

- **Django ORM** - compile to Django `QuerySet`
- **SQLModel** - likely reuse most SQLAlchemy lowering
- **Flask** - request adapter for `request.args`
