# pyrsql Reference

## Public Top-Level Exports

`pyrsql` exports:

- `parse`
- `compile`
- `apply`
- `Query`
- `Sort`
- `PageRequest`
- `QueryOptions`
- `SortOptions`
- `Backend`
- `CompilationResult`
- `SortCompilationResult`
- `PageCompilationResult`
- `ValueConverter`
- `ValueConverterRegistry`
- `FieldValueConverterSet`
- `FieldPolicySet`
- `CustomPredicateDefinition`

## Subpackages

Useful subpackages:

- `pyrsql.backends`
- `pyrsql.backends.sqlalchemy`
- `pyrsql.core`
- `pyrsql.parsing`
- `pyrsql.selector`
- `pyrsql.semantic`
- `pyrsql.sorting`

## Query Operators

Built-in comparison operators:

- `==`
- `!=`
- `=gt=`
- `=ge=`
- `=lt=`
- `=le=`
- `>`
- `>=`
- `<`
- `<=`
- `=in=`
- `=out=`
- `=na=`
- `=nn=`
- `=like=`
- `=notlike=`
- `=ic=`
- `=ilike=`
- `=inotlike=`
- `=bt=`
- `=nb=`

## Logical Operators

Supported logical composition:

- `;`
- `and`
- `,`
- `or`

## Sort Syntax

Supported forms:

- `name`
- `name,asc`
- `name,desc`
- `name,asc,ic`
- `company.name,desc`
- `@upper[name],asc`

## Current Backend Notes

### SQLAlchemy

Current backend target:

- `SQLAlchemy 2.0`
- `select(...)` API

Supported:

- filter translation
- sort translation
- pagination
- `distinct`
- `join_hints`
- custom predicates
- field mapping and ACL
- field-specific and type-specific conversion
- PostgreSQL-style JSON / JSONB path filtering and sorting

Not currently supported:

- framework adapters
- non-SQLAlchemy backends
- backend-neutral JSON configuration
- advanced temporal JSON semantics
