# Testing Strategy

## Goals

The `pyrsql` test suite is organized by **test responsibility**, not by
technology alone. The structure should make it obvious:

- what is being tested
- at which isolation level it is being tested
- which tests are safe to run by default
- which tests are intended for regression detection, hardening, or benchmarking

## Test layers

### `unit`

Unit tests validate one module, class, or narrow behavior in isolation.

Rules:

- unit tests mirror `src/pyrsql`
- each test module should map clearly to one implementation module
- avoid real database or end-to-end ORM flows
- prefer direct construction of objects over full public API orchestration

### `integration`

Integration tests validate interaction between components.

Rules:

- organize by pipeline or subsystem, not by source file
- allow multiple project layers to participate in one test
- ORM-specific integration tests may use real SQLAlchemy models

### `functional`

Functional tests validate user-visible library behavior.

Rules:

- organize by feature or capability
- use public API where possible
- focus on behavior and regressions, not internals

### `performance`

Performance tests validate that hot paths do not regress.

Rules:

- do not treat them as correctness tests
- mark them explicitly
- keep them out of the default fast feedback loop

### `security`

Security tests validate that hostile or malformed input is handled safely.

Rules:

- use offensive payloads deliberately
- assert stable failure modes, not only success paths
- validate both SQL/statement shape and HTTP error shape where relevant
- keep one attack contract per test

Current `security` coverage includes:

- scalar SQL injection payloads treated as bound values
- structural field/function abuse rejected by allowlists and blocklists
- parser and sort complexity limits
- JSONPATH and `like_regex` escaping
- duplicate query parameter handling at the FastAPI boundary
- non-verbose error payloads

## Fixtures and helpers

### `conftest.py` hierarchy

`pyrsql` uses per-folder `conftest.py` files for scoped fixtures:

| Level | Purpose |
|-------|---------|
| `tests/conftest.py` | Shared between all test packages |
| `tests/unit/.../conftest.py` | Unit-scoped fakes and local helpers |
| `tests/integration/sqlalchemy/conftest.py` | Shared SQLAlchemy models, `orm`, PostgreSQL dialect helpers |
| `tests/functional/fastapi_sqlalchemy/conftest.py` | Shared SQLAlchemy models for FastAPI integration tests |
| `tests/security/conftest.py` | Shared FastAPI app factories and response-sanitization helpers |
| `tests/performance/conftest.py` | Shared benchmark fixtures and models |

Create a local `conftest.py` when it removes real repetition. Avoid using it
to hide the main action of the test.

## Pytest markers

Registered markers:

- `unit`
- `integration`
- `functional`
- `performance`
- `security`
- `sqlalchemy`
- `fastapi`

Examples:

```bash
uv run pytest -m security
uv run pytest -m "functional and fastapi"
uv run pytest -m "integration and sqlalchemy"
```

## Async validation

Async support is validated at three levels:

- adapter behavior on `async def` routes
- SQLAlchemy pipeline execution with `AsyncSession`
- FastAPI + SQLAlchemy end-to-end async integration

Typical commands:

```bash
uv run pytest tests/functional/fastapi_adapter/test_async_dependency.py -q
uv run pytest tests/integration/sqlalchemy/test_async_pipeline.py -q
uv run pytest tests/functional/fastapi_sqlalchemy/test_async_integration.py -q
```

## Free-threaded validation

Free-threaded correctness depends primarily on avoiding unsynchronized access to
shared mutable state.

In `pyrsql`, the main targets are:

- integration dependency caches
- SQLAlchemy model-introspection caches
- resolver caches

Recommended validation flow:

```bash
uv run pytest \
  tests/unit/integrations/fastapi_sqlalchemy/test_integration.py \
  tests/unit/orms/sqlalchemy/test_resolver.py -q
```

When a free-threaded CPython build is available locally, rerun with the GIL
disabled. Example:

```bash
PYTHON_GIL=0 python -m pytest \
  tests/unit/integrations/fastapi_sqlalchemy/test_integration.py \
  tests/unit/orms/sqlalchemy/test_resolver.py -q
```

## Security validation

Recommended commands:

```bash
uv run pytest tests/security -q
uv run pytest -m security
```

The security suite is intentionally broader than “SQL injection only”. It also
covers:

- resource-consumption limits
- invalid structural selectors
- JSON path escaping
- duplicate parameter handling
- sanitized integration errors

## Design notes

Testing follows a few explicit conventions:

- one behavior per test
- Arrange / Act / Assert should stay obvious
- use fixtures for shared setup, not for hiding assertions
- prefer public APIs in functional/security tests
- keep backend assertions narrow and stable
