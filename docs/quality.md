# pyrsql Quality and Tooling

## Standards

`pyrsql` follows:

- Google Python Style Guide
- `pylint` using the Google `pylintrc`
- `pytest` for unit and integration tests
- `mypy` for static typing
- `black` and `isort` for formatting and import organization

## Practical Decisions

- Use package imports instead of importing individual functions into modules
  when module scoping communicates ownership more clearly.
- Keep public APIs small and explicit.
- Prefer immutable value objects for backend-neutral domain concepts.
- Use `Protocol` and `ABC` for stable contracts where backends plug into the
  core.
- Keep the backend-neutral core free from ORM-specific dependencies.

## Initial Commands

Representative local commands:

```text
uv run pytest
uv run pylint src tests
uv run mypy src
uv run black src tests
uv run isort src tests
```
