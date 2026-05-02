## pyrsql

`pyrsql` is a backend-agnostic RSQL library for Python.

The project is being designed to support multiple backends, starting with
`SQLAlchemy 2.0`. The core package remains backend-neutral, while backend
implementations live in `backends`, and framework-specific integration lives
in `adapters`.

Current `SQLAlchemy` support includes:

- filters
- sorting
- pagination
- `distinct`
- `join_hints`
- PostgreSQL-style JSON / JSONB path support
- temporal JSON path semantics via `JSONOptions(use_datetime=True)`

## Development Principles

- Object-oriented design
- SOLID principles
- Google Python Style Guide
- Strong typing
- Backend-neutral public API

## Documentation

- [Architecture](docs/architecture.md)
- [Usage](docs/usage.md)
- [Reference](docs/reference.md)
- [Google Python Style Guide](docs/pyguide.md)
- [Quality and Tooling](docs/quality.md)
- [Testing](docs/testing.md)
