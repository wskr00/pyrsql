## pyrsql

`pyrsql` is a backend-agnostic RSQL library for Python.

The project is being designed to support multiple backends, starting with
`SQLAlchemy 2.0`. The core package remains backend-neutral, while backend
implementations live in `backends`, and framework-specific integration lives
in `adapters`.

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
