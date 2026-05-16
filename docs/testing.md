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

## Mapping Rules

Unit tests mirror the production tree. Integration tests group by pipeline.
Functional tests group by capability. Performance tests group by hotspot.

Examples:

- `src/pyrsql/core/options.py` → `tests/unit/core/test_options.py`
- `src/pyrsql/parsing/parser.py` → `tests/unit/parsing/test_parser.py`
- `src/pyrsql/orms/sqlalchemy/resolver.py` → `tests/unit/orms/sqlalchemy/test_resolver.py`

## Fixtures and Test Helpers

### `conftest.py` hierarchy

pyrsql uses per-folder `conftest.py` files for scoped fixtures:

| Level | Purpose |
|-------|---------|
| `tests/conftest.py` | Shared between all tests packages |
| `tests/unit/conftest.py` | Auto-marks `@pytest.mark.unit` on all unit tests |
| `tests/unit/core/conftest.py` | `FakeORM`, `FakeCompiledResult`, `fake_orm_factory` |
| `tests/unit/orms/sqlalchemy/conftest.py` | SQLAlchemy test models, `model_inspector`, `path_resolver`, `json_path_builder`, `postgresql_dialect` |
| `tests/unit/adapters/fastapi_adapter/conftest.py` | `query_stub`, `sort_stub`, `page_request`, `openapi_examples` |
| `tests/unit/integrations/fastapi_sqlalchemy/conftest.py` | SQLAlchemy models, `sqlalchemy_orm`, `integration`, fixture-based criteria |
| `tests/integration/sqlalchemy/conftest.py` | Shared SQLAlchemy models, `orm`, `pg_dialect`, `render_sql` helper |
| `tests/functional/fastapi_sqlalchemy/conftest.py` | Shared `Base`/`User` models |
| `tests/performance/conftest.py` | Shared test-data constants, SQLAlchemy models, `sqlalchemy_orm`, `pg_dialect` |

### Mocking patterns

Unit tests that verify **orchestration** (object A delegates to object B) use
`unittest.mock` and `pytest.monkeypatch`:

```python
from unittest.mock import Mock, sentinel

# Replacing a class method with a controlled return value
parse_mock = Mock(return_value=sentinel.EXPRESSION)
monkeypatch.setattr(Query, "parse_expression", staticmethod(parse_mock))

# Assert the mock was called correctly
parse_mock.assert_called_once_with("name==demo", options=options)
```

- **`sentinel`** replaces `object()` for named stub values - stack traces
  show `sentinel.FIELDS` instead of `<object object at 0x...>`
- **`Mock(return_value=...)`** replaces `staticmethod(lambda ...)` -
  supports `assert_called_once_with` for argument verification
- **`Mock(side_effect=...)`** replaces manual `calls: list` tracking -
  built-in call recording with `assert_has_calls`

Tests that are **pure value tests** (create object, pass input, check output)
do not use mocks - they use real instances directly.

## Pytest Markers

Registered markers (in `pyproject.toml`):

- `unit` - isolated module/class tests
- `integration` - cross-component interaction
- `functional` - user-visible behavior via public API
- `performance` - hotspot benchmarks
- `sqlalchemy` - SQLAlchemy-dependent tests
- `fastapi` - FastAPI-dependent tests

## Free-Threaded Validation

For free-threaded Python support, correctness depends primarily on avoiding
unsynchronized access to shared mutable state. In `pyrsql`, this means:

- immutable configuration/value objects should remain shareable across threads
- caches shared by integrations and ORM helpers should use explicit locking
- tests should exercise concurrent access to those caches directly

Recommended validation flow:

```bash
uv run pytest tests/unit/integrations/fastapi_sqlalchemy/test_integration.py \
  tests/unit/orms/sqlalchemy/test_resolver.py
```

When a free-threaded CPython build is available locally, run the same tests
with the GIL disabled as part of regression checks, for example with
`PYTHON_GIL=0` or `-X gil=0` depending on how Python was installed.
