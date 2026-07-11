# pyrsql Architecture

## Identity

`pyrsql` is a compiler-oriented RSQL query engine. It turns RSQL-like filter
and sort expressions into ORM-specific statement updates through a staged
pipeline:

```text
query text
-> parsing
-> selector AST
-> semantic binding
-> backend lowering
-> ORM-specific statement
```

The core is deliberately ORM-neutral. Adding a new backend means implementing
the `ORM` interface, not rewriting the parser, selector grammar, or semantic
rules.

## Purpose

The project is designed around four major responsibilities:

- language frontend: parse text into syntax trees
- semantic binding: resolve fields, functions, and access policies
- backend lowering: turn validated query objects into ORM-specific statements
- optional framework adapters and integrations: expose the core in HTTP stacks

The current production backend is SQLAlchemy 2.0. The current framework
adapter is FastAPI.

## Current Pipeline

More concretely, the runtime flow looks like this:

```text
RSQL string
-> parsing AST
-> selector nodes
-> SemanticBinder / SortBinder
-> Query / Sort / PageRequest application
-> SQLAlchemyORM lowering
-> SQLAlchemy Select
```

For pagination-only flows, `PageRequest` goes directly to backend lowering.

## Module Boundaries

The project is split into these main modules:

- `parsing`
- `selector`
- `semantic`
- `sorting`
- `core`
- `orms`
- `adapters`
- `integrations`
- `api`

### `parsing`

Owns:

- source spans
- tokens
- parser AST
- parser limits
- parse diagnostics and errors

### `selector`

Owns selector syntax only:

- `FieldSelector`
- `LiteralSelector`
- `FunctionSelector`

It does not own semantic meaning.

### `semantic`

Owns semantic binding:

- field policy checks
- function policy checks
- field mapping
- semantic diagnostics and errors
- normalization for backend lowering

### `sorting`

Owns sort syntax and sort binding.

### `core`

Owns user-facing ORM-agnostic objects:

- `Query`, `Sort`, `PageRequest`
- `QueryOptions`, `SortOptions`
- `FieldPolicySet`, `ProcedureAccessPolicy`
- `CustomPredicateDefinition`
- `ValueConverterRegistry`, `FieldValueConverterSet`
- `JSONOptions`, `JSONSortScalarType`
- `JSONPath`, `JSONPathComparison`
- `JSONScalarNormalizer`, `JSONScalarValue`
- `JoinHint`

The `core/json/` package owns JSON-aware comparison models and value
normalization, keeping JSON semantics ORM-neutral.

### `orms`

Owns backend lowering.

Current production backend:

- `orms.sqlalchemy`

Its job is:

- consume normalized query, sort, and page objects
- resolve model metadata
- coerce values
- lower to SQLAlchemy statements

It should not redo semantic interpretation already handled upstream.

For PostgreSQL JSON/JSONB lowering, the current design separates:

- whole-document JSON predicates
- nested JSON path predicates
- JSON sort extraction rules

This keeps the backend close to SQLAlchemy and PostgreSQL primitives instead of
forcing every JSON case through one generic lowering path.

### `adapters`

Own framework-level request and error adaptation.

Current adapter:

- `adapters.fastapi`

It is responsible for:

- extracting query params
- building `RequestCriteria`
- translating pyrsql failures into framework-native HTTP errors
- adding OpenAPI metadata

### `integrations`

Own stack-specific orchestration across adapter + backend.

Current integration:

- `integrations.fastapi.sqlalchemy`

It is responsible for:

- request criteria application helpers
- route-ready dependencies
- declarative resource configuration
- stack-specific DX

### `api`

Owns the smallest public helper surface:

- `parse(...)`
- `compile(...)`
- `apply(...)`

## Extensibility

### Adding a new ORM backend

Implement `pyrsql.orms.base.ORM`:

```python
class ORM(ABC):
    def compile_query(self, query: Query) -> CompiledArtifact: ...
    def compile_sort(self, sort: Sort) -> CompiledArtifact: ...
    def compile_page_request(self, page_request: PageRequest) -> CompiledArtifact: ...
```

Each method receives one ORM-neutral core object and returns a compiled object
with an `apply(target, model)` method.

### Adding a new framework adapter

Implement `pyrsql.adapters.*` to extract query parameters from requests and
translate pyrsql failures into framework-native HTTP responses.

The FastAPI adapter is the reference implementation.

## Design Principles

The project follows:

- object-oriented design
- SOLID
- strong typing
- backend-independent core semantics
- performance-oriented data modeling
- explicit concurrency boundaries

### Practical interpretation

- semantic work should happen before the ORM backend
- ORMs should do lowering, not semantic analysis
- adapters should do transport adaptation, not query semantics
- integrations should provide DX, not execution frameworks

## Performance Direction

The project uses `msgspec` where it improves compactness and immutable data
modeling:

- diagnostics
- parser/source structures
- adapter and integration payloads
- core query/sort/options/value-policy models

Other performance principles:

- cache repeated base statements when safe
- avoid repeating semantic work in the ORM backend
- keep shared cache lock scope small in concurrency-sensitive paths

## Async and Free-Threaded Support

These are related but separate concerns:

- async support means generated SQLAlchemy statements work with both `Session`
  and `AsyncSession`
- free-threaded support means shared mutable caches are synchronized explicitly

The core query pipeline stays synchronous and ORM-neutral in both cases.
