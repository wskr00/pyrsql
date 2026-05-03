# pyrsql Quality and Tooling

## Standards

`pyrsql` follows:

- Google Python Style Guide
- `pylint` using the Google `pylintrc`
- `pytest` for unit and integration tests
- `mypy` for static typing
- `ruff` for formatting, import organization, and fast linting

## Practical Decisions

- Use package imports instead of importing individual functions into modules
  when module scoping communicates ownership more clearly.
- Keep public APIs small and explicit.
- Prefer immutable value objects for orm-neutral domain concepts.
- Use `Protocol` and `ABC` for stable contracts where ORMs plug into the
  core.
- Keep the orm-neutral core free from ORM-specific dependencies.

## Continuous Quality Direction

`pyrsql` is intentionally being refined beyond "works correctly". The project
should continuously improve in three areas:

- object-oriented design quality
- SOLID compliance
- performance in real hot paths

This applies especially to the orm-neutral core, where shortcuts create
long-term design debt more quickly.

## Technical Backlog

The following items are explicitly tracked as quality work, even when the
current implementation is functionally correct.

### Core Conversion Extensibility

The current value conversion flow contains a special-case branch for
`datetime` conversion in
[src/pyrsql/core/conversion.py](/home/lucas/pyrsql/src/pyrsql/core/conversion.py).

That behavior is pragmatic, but it is not the ideal design because:

- it creates asymmetry inside `ValueConverterRegistry`
- it weakens the Open/Closed Principle
- it makes future datetime policies harder to extend cleanly

The desired direction is:

- remove the hardcoded `datetime` branch from `ValueConverterRegistry.convert`
- register `datetime` conversion as a normal strategy in the registry
- preserve current ISO parsing and `date -> datetime` fallback behavior
- then extend date/time formatting through configuration rather than central
  branching

### Configurable Date and Datetime Formats

The project should support additional date/time formats without forcing
application code to override everything manually.

The preferred direction is:

- keep ISO formats as the default behavior
- allow extra configured formats for `date`, `time`, and `datetime`
- keep field-level and model-field-level overrides available for precise cases

### Performance Discipline

External dependencies may be adopted when they produce a clear improvement in
measured hot paths.

Current examples already validated in the project:

- `ciso8601` for datetime parsing
- `msgspec` for JSON literal encoding and decoding

This project should continue to prefer benchmark-backed performance changes
over speculative micro-optimizations.

## Initial Commands

Representative local commands:

```text
uv run pytest
uv run pylint src tests
uv run mypy src
uv run ruff check --fix src tests
uv run ruff format src tests
```
