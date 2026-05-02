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

## Current Directory Layout

```text
tests/
  conftest.py
  fixtures/
    __init__.py
    orms.py
    query_samples.py
    sqlalchemy_models.py

  unit/
    core/
      json/
    orms/
      sqlalchemy/
    parsing/
    selector/
    semantic/
    sorting/

  integration/
    sqlalchemy/

  functional/
    test_public_api.py

  performance/
    test_parser_bench.py
    test_selector_bench.py
    test_semantic_bench.py
    test_sqlalchemy_translation_bench.py
```

Current notable mappings:

- `tests/unit/core/...` mirrors the `core` package
- `tests/unit/parsing/...` mirrors the `parsing` package
- `tests/unit/orms/sqlalchemy/test_resolver.py` covers isolated path
  resolution and model inspection
- `tests/integration/sqlalchemy/...` covers public pipeline interaction with
  `SQLAlchemy`
- `tests/functional/test_public_api.py` covers package-level public API
- `tests/performance/...` covers regression-oriented hotspot benchmarks

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

Current examples:

- `tests/integration/sqlalchemy/test_query_pipeline.py`
- `tests/integration/sqlalchemy/test_sort_pipeline.py`
- `tests/integration/sqlalchemy/test_page_pipeline.py`

### Functional tests

Functional tests should be grouped by capability.

Current example:

- `tests/functional/test_public_api.py`

### Performance tests

Performance tests should be grouped by hotspot.

Current examples:

- `tests/performance/test_parser_bench.py`
- `tests/performance/test_selector_bench.py`
- `tests/performance/test_semantic_bench.py`
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

They are skipped by default and must be requested explicitly with:

```bash
pytest tests/performance --run-performance
```

## Status

The suite now has all four layers in place:

1. `unit`
2. `integration`
3. `functional`
4. `performance`

Further work should focus on refining boundaries within those layers rather
than changing the top-level testing model.
