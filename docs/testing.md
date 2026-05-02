# Testing Strategy

## Goals

The `pyrsql` test suite is organized by **test responsibility**, not by
technology alone. The structure should make it obvious:

- what is being tested
- at which isolation level it is being tested
- which tests are safe to run by default
- which tests are intended for regression detection or benchmarking

## Test Layers

### `unit`

Unit tests validate one module, class, or narrow behavior in isolation.

Rules:

- unit tests mirror `src/pyrsql`
- each test module should map clearly to one implementation module
- avoid real database or end-to-end ORM flows
- prefer direct construction of objects over full public API orchestration

Examples:

- `src/pyrsql/parsing/lexer.py`
- `tests/unit/parsing/test_lexer.py`

- `src/pyrsql/core/json/path.py`
- `tests/unit/core/json/test_path.py`

### `integration`

Integration tests validate interaction between components.

Rules:

- organize by pipeline or subsystem, not by source file
- allow multiple project layers to participate in one test
- ORM-specific integration tests may use real SQLAlchemy models or
  in-memory database setup

Examples:

- parser -> semantic analyzer -> ORM compiler
- query object -> SQLAlchemy ORM -> `Select`
- JSON path resolution -> SQLAlchemy translation

### `functional`

Functional tests validate user-visible library behavior.

Rules:

- organize by feature or capability
- use public API where possible
- focus on behavior and regressions, not internals

Examples:

- filtering behavior
- sorting behavior
- pagination behavior
- JSON behavior
- error message behavior

### `performance`

Performance tests validate that hot paths do not regress.

Rules:

- never rely on them as correctness tests
- mark them explicitly
- keep them out of the default fast feedback loop
- measure representative workloads rather than micro-optimizing blindly

Examples:

- lexer throughput
- parser throughput
- selector parsing throughput
- semantic normalization throughput
- SQLAlchemy translation throughput

## Planned Directory Layout

```text
tests/
  conftest.py
  fixtures/
    __init__.py
    ORMs.py
    query_samples.py
    sqlalchemy_models.py

  unit/
    core/
    parsing/
    selector/
    semantic/
    sorting/
    orms/sqlalchemy/

  integration/
    api/
    sqlalchemy/

  functional/

  performance/
```

## Mapping Rules

### Unit tests

Unit tests should mirror the production tree.

Examples:

- `src/pyrsql/core/options.py`
  -> `tests/unit/core/test_options.py`
- `src/pyrsql/parsing/parser.py`
  -> `tests/unit/parsing/test_parser.py`
- `src/pyrsql/orms/sqlalchemy/translator.py`
  -> `tests/unit/orms/sqlalchemy/test_translator.py`

### Integration tests

Integration tests should be grouped by interaction boundary.

Examples:

- `tests/integration/api/test_query_to_sqlalchemy.py`
- `tests/integration/sqlalchemy/test_json_pipeline.py`
- `tests/integration/sqlalchemy/test_value_conversion_pipeline.py`

### Functional tests

Functional tests should be grouped by capability.

Examples:

- `tests/functional/test_rsql_filtering.py`
- `tests/functional/test_sorting_behavior.py`
- `tests/functional/test_json_behavior.py`

### Performance tests

Performance tests should be grouped by hotspot.

Examples:

- `tests/performance/test_lexer_bench.py`
- `tests/performance/test_parser_bench.py`
- `tests/performance/test_sqlalchemy_translation_bench.py`

## Fixtures

Fixtures should be centralized when they are shared across multiple test
layers or multiple modules.

### `tests/conftest.py`

Use for:

- lightweight global fixtures
- pytest hooks or markers
- common assertion helpers that truly apply across the suite

### `tests/fixtures/`

Use for reusable domain-specific fixtures such as:

- SQLAlchemy models for ORM tests
- sample query and sort payloads
- ORM factory helpers

Avoid hiding important fixture setup in unrelated test modules.

## Pytest Markers

The suite should use explicit markers:

- `unit`
- `integration`
- `functional`
- `performance`
- `sqlalchemy`

`performance` tests should not be part of the default quick test loop.

## Migration Plan

The migration should happen incrementally.

1. Keep the current suite green at all times.
2. Create the new top-level test infrastructure first.
3. Move unit tests into a mirrored `tests/unit/...` layout.
4. Split current mixed ORM tests into:
   - unit tests
   - integration tests
   - functional tests
5. Add a dedicated performance layer last.

During migration, temporary coexistence between old and new file layout is
acceptable if it avoids risky large-batch moves.
