# pyrsql Architecture

## Purpose

`pyrsql` compiles an RSQL-like query language into ORM-specific query objects.

The project is designed around:

- a language frontend
- semantic binding
- a logical IR
- backend lowering
- optional framework adapters and integrations

The current production backend is `SQLAlchemy 2.0`.

## Current Pipeline

The internal pipeline is:

```text
query text
-> parsing
-> selector AST
-> semantic binding
-> logical IR
-> ORM lowering
-> ORM-specific statement
```

More concretely:

```text
RSQL string
-> parser AST
-> SemanticBinder / SortBinder
-> Bound IR
-> SQLAlchemyORM lowering
-> SQLAlchemy Select
```

This is not just a parser. It is a small DSL compiler for query backends.

## Module Boundaries

The project is split into these main modules:

- `parsing`
- `selector`
- `semantic`
- `sorting`
- `ir`
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
- translation from AST to logical IR

### `sorting`

Owns sort syntax and sort binding.

### `ir`

Owns the backend-independent logical representation:

- bound query nodes
- bound sort nodes
- bound page node

This IR is the contract between semantic binding and ORM lowering.

### `core`

Owns user-facing ORM-agnostic objects:

- `Query`
- `Sort`
- `PageRequest`
- `QueryOptions`
- `SortOptions`
- conversion and policy infrastructure
- JSON options and JSON helper types

### `orms`

Owns backend lowering.

Current production backend:

- `orms.sqlalchemy`

Its job is:

- consume bound IR
- resolve model metadata
- coerce values
- lower to SQLAlchemy statements

It should not redo semantic interpretation already handled upstream.

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
- stack-specific product DX

### `api`

Owns the smallest public helper surface:

- `parse(...)`
- `compile(...)`
- `apply(...)`

## Design Principles

The project follows:

- object-oriented design
- SOLID
- strong typing
- explicit invariants
- backend-independent core semantics
- performance-oriented data modeling

### Practical interpretation

- semantic work should happen before the ORM backend
- ORMs should do lowering, not semantic analysis
- adapters should do transport adaptation, not query semantics
- integrations should provide DX, not execution frameworks

## Performance Direction

The project uses `msgspec` aggressively where it helps:

- compact immutable records
- diagnostics
- IR nodes
- parser/source structures
- adapter and integration payloads

Other performance principles:

- cache repeated base statements when safe
- avoid repeating semantic work in the ORM backend
- keep hot-path allocations small
- prefer explicit invariants over defensive branching spread everywhere

## FastAPI Product Layer

The FastAPI story now has three layers:

### Adapter layer

`adapters.fastapi`

Provides:

- `FastAPICriteriaConfig`
- `CriteriaDependency`
- `RequestCriteria`

### Integration layer

`integrations.fastapi.sqlalchemy`

Provides:

- `FastAPISQLAlchemyIntegration`
- `FastAPISQLAlchemyResource`
- `SQLAlchemyPaginatedSelect`

### Resource layer

`integration.resource(...)`

Provides declarative endpoint-oriented configuration:

- filterable fields
- sortable fields
- default sort
- max page size
- OpenAPI examples
- `statement_factory`
- route-ready dependencies

This is the current productized FastAPI interface.

## Current Public Direction

The public API is intentionally small and ORM-neutral at the top level.

Top-level public names include:

- `parse`
- `compile`
- `apply`
- `Query`
- `Sort`
- `PageRequest`

Framework and backend integrations live in subpackages, not in `pyrsql.__init__`.

## Out of Scope

The project intentionally does not provide:

- automatic query execution
- repository abstractions
- response serialization
- export/summarization helpers
- non-SQLAlchemy backend implementations yet

## Future Direction

Planned long-term areas include:

- richer diagnostics
- additional ORMs
- SQLAlchemy-driven OpenAPI example generation
- more ergonomic integration helpers where justified

Rewrite and optimizer-style passes remain a future concern, not a current
priority. The present architecture is centered on:

```text
parse -> bind -> IR -> lower
```
