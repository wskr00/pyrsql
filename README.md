## pyrsql

`pyrsql` is an ORM-oriented RSQL library for Python.

The project is being designed to support multiple ORMs, starting with
`SQLAlchemy 2.0`. The core package remains ORM-neutral, while ORM
implementations live in `orms`, and framework-specific integration lives
in `adapters`.

Current `SQLAlchemy` support includes:

- filters
- sorting
- pagination
- `distinct`
- `join_hints`
- PostgreSQL-style JSON / JSONB path support
- temporal JSON path semantics via `JSONOptions(use_datetime=True)`

Current adapter support includes:

- `FastAPI` request extraction via dependencies
- configurable `filter`, `sort`, `page`, and `size` parameters
- class-based and factory-based FastAPI dependencies
- `HTTP 422` translation for pyrsql parse and semantic failures

## Development Principles

- Object-oriented design
- SOLID principles
- Google Python Style Guide
- Strong typing
- ORM-neutral public API

## Documentation

- [Architecture](docs/architecture.md)
- [Usage](docs/usage.md)
- [Reference](docs/reference.md)
- [FastAPI Adapter Usage](docs/usage.md#fastapi-adapter)
- [Google Python Style Guide](docs/pyguide.md)
- [Quality and Tooling](docs/quality.md)
- [Testing](docs/testing.md)
