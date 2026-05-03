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
- `ORM`
- `CompilationResult`
- `SortCompilationResult`
- `PageCompilationResult`
- `ValueConverter`
- `ValueConverterRegistry`
- `FieldValueConverterSet`
- `FieldPolicySet`
- `CustomPredicateDefinition`
- `JSONOptions`

## Subpackages

Useful subpackages:

- `pyrsql.orms`
- `pyrsql.orms.sqlalchemy`
- `pyrsql.core`
- `pyrsql.parsing`
- `pyrsql.selector`
- `pyrsql.semantic`
- `pyrsql.sorting`
- `pyrsql.adapters`
- `pyrsql.adapters.fastapi`
- `pyrsql.integrations`
- `pyrsql.integrations.fastapi`

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

## Current ORM Notes

### SQLAlchemy

Current ORM target:

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
- `JSONOptions(use_datetime=...)` for temporal JSON path semantics
- configurable JSON path function names via `JSONOptions`

Not currently supported:

- framework adapters
- non-SQLAlchemy ORMs

## FastAPI Adapter

`pyrsql.adapters.fastapi` exports:

- `FastAPICriteriaConfig`
- `RequestCriteria`
- `CriteriaDependency`
- `criteria_dependency(...)`

### FastAPICriteriaConfig

Supported configuration:

- `filter_parameter`
- `sort_parameter`
- `page_parameter`
- `size_parameter`
- `default_page_size`
- `max_page_size`
- `one_based_paging`
- `query_options`
- `sort_options`

Derived properties:

- `minimum_page_number`
- `default_page_number`

### RequestCriteria

Carries:

- `query`
- `sort`
- `page_request`

Methods:

- `apply(target, model, orm=...)`

Properties:

- `is_empty`

### CriteriaDependency

A callable FastAPI dependency object that exposes a generated request
signature and returns `RequestCriteria`.

### criteria_dependency(...)

Convenience factory that returns `CriteriaDependency`.

## FastAPI + SQLAlchemy Integration

`pyrsql.integrations.fastapi` exports:

- `FastAPISQLAlchemyIntegration`
- `SQLAlchemyPaginatedSelect`

### FastAPISQLAlchemyIntegration

Constructor arguments:

- `orm`
- `criteria_config`

Methods:

- `criteria_dependency()`
- `apply(statement, model, criteria)`
- `select(model, criteria)`
- `select_dependency(model)`
- `count_select(model, criteria)`
- `count_select_dependency(model)`
- `paginated_select(model, criteria)`
- `paginated_select_dependency(model)`

### SQLAlchemyPaginatedSelect

Carries:

- `statement`
- `count_statement`
