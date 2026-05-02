# pyrsql Architecture and Project Decisions

## Purpose

`pyrsql` is a Python library that translates RSQL-like queries into
ORM-specific query objects.

The project is being designed from the start to support multiple ORMs in
the future, such as:

- `SQLAlchemy`
- `Django ORM`
- other ORMs if they fit the abstraction model

The initial implementation target is `SQLAlchemy 2.0`.

## Current Scope

The current focus is:

- define the project architecture correctly before implementation
- keep the core ORM-oriented
- implement the first production ORM for `SQLAlchemy 2.0`

The following items are intentionally out of the MVP:

- `JSON` / `JSONB`
- additional ORMs
- exact feature parity with `rsql-jpa`

## High-Level Product Direction

`pyrsql` should be:

- object-oriented
- strongly typed
- extensible
- safe by default
- performant
- easy to understand and maintain

The API should use clean, stable, high-level names. ORM-specific behavior
must not leak into the public API naming unnecessarily.

## Core Architecture Principle

The project must be split into:

- a ORM-oriented core
- one or more ORM implementations
- one or more framework adapters

The core must not import or depend on `SQLAlchemy` or any other ORM
implementation.

ORMs depend on the core, not the other way around.

Framework adapters also depend on the core, and may depend on one or more
ORMs.

This separation is required so that:

- `pip install pyrsql` installs only the core
- `pip install pyrsql[sqlalchemy]` enables SQLAlchemy integration
- `pip install pyrsql[fastapi,sqlalchemy]` enables HTTP adapter plus query
  ORM
- future ORMs can be added without restructuring the project

## Architectural Style

The project will follow:

- object-oriented design
- SOLID principles
- Google Python Style Guide

### SOLID Interpretation for `pyrsql`

#### Single Responsibility Principle

Each major concern must live in its own component. For example:

- lexical analysis
- parsing
- AST modeling
- semantic validation
- type coercion
- ORM translation
- ORM application to a query object
- framework request and error adaptation

#### Open/Closed Principle

The system must be open for extension through new ORMs, adapters, and
custom strategies, while avoiding modification of the core design when new
capabilities are introduced.

#### Liskov Substitution Principle

ORM integrations must honor clear behavioral contracts so one ORM implementation
can be replaced by another without breaking the API semantics.

#### Interface Segregation Principle

Interfaces must remain small and focused. Avoid one oversized abstraction that
handles parsing, semantic analysis, translation, and execution concerns at
once.

#### Dependency Inversion Principle

The core must depend on abstractions, such as `Protocol` or `ABC` contracts,
rather than concrete ORM implementations.

## Public API Direction

The public API should remain small, expressive, and orm-neutral.

Preferred public names:

- `parse(...)`
- `compile(...)`
- `apply(...)`

The naming of public functions should not vary by orm. For example, avoid
names such as:

- `apply_sqlalchemy(...)`
- `compile_django(...)`

Instead, ORM specialization should happen through injected ORM objects
or ORM-specific configured objects.

## Object-Oriented API Direction

The project should prefer high-level object-oriented composition over a purely
procedural style.

Representative domain objects may include:

- `Query`
- `QueryOptions`
- `CompilationResult`
- `ORM`

Potential style directions include:

```python
query = Query.parse("name==john")
compiled = query.compile(orm=orm)
stmt = compiled.apply(stmt, model=User)
```

or:

```python
stmt = apply(stmt, User, "name==john", orm=orm)
```

The exact public surface can still be refined, but it must stay:

- cohesive
- orm-neutral in naming
- explicit in contracts

## Parser Strategy

The parser will be built in-house rather than relying on an external RSQL
parser package.

### Parser goals

- high performance
- memory efficiency
- strong control over syntax and error handling
- secure behavior under malformed or adversarial input

### Parser design direction

- custom lexer
- custom parser
- immutable AST nodes
- configurable safety limits

Possible safety controls include:

- maximum query length
- maximum nesting depth
- maximum AST node count
- maximum argument count

## ORM Strategy

The first ORM is `SQLAlchemy 2.0`.

Important constraints:

- use the `2.0` query model
- target `select(...)` workflows
- do not design around legacy `Query`

Future ORMs are expected, including `django`, but the current
implementation work should optimize for `SQLAlchemy` first without
contaminating the core abstractions.

## Adapter Strategy

Framework-specific integration should live in adapters rather than ORMs.

Examples:

- `adapters.fastapi`
- `adapters.django`

The adapter layer is responsible for:

- request extraction
- transport-specific validation behavior
- transport-specific error conversion
- convenient binding to framework primitives

Adapters must not own the query language semantics. They orchestrate the core
and selected ORM for a specific runtime environment.

## Packaging Strategy

The package name is `pyrsql`.

The project should support optional ORM installations through extras:

```text
pip install pyrsql[sqlalchemy]
```

Future examples:

```text
pip install pyrsql[django]
pip install pyrsql[fastapi,sqlalchemy]
```

### Packaging rules

- base package contains only the core and shared abstractions
- ORM dependencies are optional
- adapter dependencies are optional
- development tooling lives in a separate extra

Representative `pyproject.toml` direction:

```toml
[project.optional-dependencies]
sqlalchemy = ["sqlalchemy>=2.0"]
fastapi = ["fastapi>=0.110"]
django = ["django>=5.0"]
dev = ["pytest", "pylint", "mypy", "black", "isort"]
```

## Project Structure Direction

The package should be prepared for multiple ORMs from the beginning.

Suggested structure:

```text
src/pyrsql/
  __init__.py
  api/
  core/
  parsing/
  orms/
    base.py
    sqlalchemy/
      __init__.py
      orm.py
      translator.py
      resolver.py
    django/
      __init__.py
      orm.py
      translator.py
      resolver.py
  adapters/
    fastapi/
      __init__.py
      dependency.py
      errors.py
    django/
      __init__.py
      request.py
      errors.py
  errors.py

docs/
tests/
  unit/
  integration/
```

This structure can still evolve, but the major boundaries should remain stable.

## Core Components

The ORM-oriented core is expected to contain:

- operators and operator metadata
- lexer
- parser
- AST
- semantic validation
- property remapping support
- whitelist and blacklist support
- type coercion infrastructure
- shared exceptions
- query and compilation abstractions

## ORM Components

The `SQLAlchemy` ORM is expected to contain:

- path resolution
- relationship and join planning
- AST to predicate translation
- application of compiled output to a `Select`

The ORM layer should handle ORM-specific behavior without leaking those
details into the core model.

Future ORMs are expected to follow the same responsibility split,
including `django` as a query orm.

## Adapter Components

Adapters are separate from ORM implementations.

Examples:

- `adapters.fastapi`
- `adapters.django`

Adapters should contain framework-facing concerns such as:

- extracting query text from requests
- mapping parsing and validation failures to framework errors
- offering convenience helpers for framework-native usage

An adapter may depend on a orm, but an ORM must not depend on an
adapter.

## Quality Standards

The project must be built with strict quality gates from the beginning.

Required tooling direction:

- `pytest`
- `pylint`
- `mypy`
- `black`
- `isort`

Additional quality expectations:

- strong unit coverage for core logic
- integration tests for ORM behavior
- clear exception model
- good internal naming
- minimal accidental complexity

## Code Style and Language Conventions

The baseline style reference is the Google Python Style Guide.

Key practical implications:

- clear names
- readable structure
- explicit responsibilities
- consistent docstrings
- predictable formatting
- typed interfaces where useful

Python features should be used when they improve correctness, readability,
architecture, or performance.

Examples of acceptable advanced usage:

- `dataclasses`
- `slots`
- `Protocol`
- `ABC`
- generics
- immutable value objects where appropriate

These features must be used deliberately, not performatively.

## Design Preferences

The project should avoid:

- giant procedural helper modules
- ORM-specific logic in the core
- adapter-specific transport logic in the core
- unstable or overly clever APIs
- naming that changes by ORM
- unnecessary exact compatibility constraints with `rsql-jpa`

The project should favor:

- explicit domain objects
- narrow contracts
- composition
- immutability where it helps
- extension points that do not distort the core model

## MVP Functional Direction

The first implementation phase should focus on:

- query parsing
- AST generation
- semantic validation
- SQLAlchemy 2.0 translation
- high-quality tests

Representative operator coverage for the MVP:

- equality and inequality
- comparison operators
- `IN` / `NOT IN`
- null checks
- `LIKE` / case-insensitive `LIKE`
- boolean composition with `AND` / `OR`
- parentheses

The operator set does not need to be a perfect clone of the Java project as
long as the model is coherent and useful.

## Deferred Features

These items are intentionally postponed:

- `JSON` / `JSONB`
- secondary ORMs
- advanced ORM-specific features that would distort the initial
  architecture

## Documentation Direction

The project should keep a dedicated `docs/` folder.

Documentation should capture:

- architecture decisions
- public API decisions
- packaging decisions
- coding standards
- testing standards
- implementation phases

This file is the initial consolidation of the decisions made before coding
begins.
