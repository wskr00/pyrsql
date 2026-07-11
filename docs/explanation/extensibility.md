# Extensibility

`pyrsql` is designed to support multiple ORM backends and framework adapters.
The core (`pyrsql.core`, `pyrsql.parsing`, `pyrsql.semantic`,
`pyrsql.sorting`) has zero dependencies on any ORM or framework.

## Adding a new ORM backend

Implement the `ORM` abstract base class:

```python
from pyrsql.core.compiler import CompiledArtifact
from pyrsql.orms.base import ORM

class MyORM(ORM):
    def compile_query(self, query: Query) -> CompiledArtifact:
        ...

    def compile_sort(self, sort: Sort) -> CompiledArtifact:
        ...

    def compile_page_request(self, page_request: PageRequest) -> CompiledArtifact:
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

### `CompiledArtifact`

```python
class CompiledArtifact(Protocol):
    def apply(self, target: _TargetT, model: type[_ModelT]) -> _TargetT: ...
```

Receives an ORM-specific target and model class, then returns the modified
target with query conditions applied.

The same contract applies to query, sort, and pagination artifacts such as
`LIMIT` and `OFFSET`.

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
