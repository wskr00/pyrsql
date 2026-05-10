# pyrsql Reference

- [Public Top-Level Exports](#public-top-level-exports)
- [QueryOptions](#queryoptions)
- [SortOptions](#sortoptions)
- [Query Operators](#query-operators)
- [Logical Operators](#logical-operators)
- [Sort Syntax](#sort-syntax)
- [JSON Options & Types](#json-options--types)
- [Current ORM Notes](#current-orm-notes)
- [FastAPI Adapter](#fastapi-adapter)
- [FastAPI + SQLAlchemy Integration](#fastapi--sqlalchemy-integration)
- [Subpackages](#subpackages)

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
- `ProcedureAccessPolicy`
- `CustomPredicateDefinition`
- `JSONOptions`
- `DEFAULT_JSON_OPTIONS`
- `JSONSortScalarType`
- `JSONPath`
- `JSONPathComparison`
- `JSONScalarNormalizer`
- `JSONScalarValue`

## Subpackages

Useful subpackages:

- `pyrsql.orms`
- `pyrsql.orms.sqlalchemy`
- `pyrsql.core`
- `pyrsql.ir`
- `pyrsql.parsing`
- `pyrsql.selector`
- `pyrsql.semantic`
- `pyrsql.sorting`
- `pyrsql.adapters`
- `pyrsql.adapters.fastapi`
- `pyrsql.integrations`
- `pyrsql.integrations.fastapi`
- `pyrsql.integrations.fastapi.sqlalchemy`

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

## QueryOptions

Configuration fields for `Query.parse(...)`:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `strict_equality` | `bool` | `False` | Disable wildcard matching in `==` |
| `distinct` | `bool` | `False` | `SELECT DISTINCT` |
| `like_escape_character` | `str\|None` | `None` | LIKE escape char (single char) |
| `field_mapping` | `Mapping[str,str]` | `{}` | Global field aliases |
| `model_field_mapping` | `Mapping[type,Mapping[str,str]]` | `{}` | Per-model aliases |
| `join_hints` | `Mapping[str,JoinHint]` | `{}` | Relationship join hints |
| `field_whitelist` | `frozenset[str]` | `frozenset()` | Allowed field paths |
| `field_blacklist` | `frozenset[str]` | `frozenset()` | Blocked field paths |
| `model_field_whitelist` | `Mapping[type,frozenset[str]]` | `{}` | Per-model allowed fields |
| `model_field_blacklist` | `Mapping[type,frozenset[str]]` | `{}` | Per-model blocked fields |
| `procedure_whitelist` | `tuple[str,...]` | `()` | Allowed function patterns (regex) |
| `procedure_blacklist` | `tuple[str,...]` | `()` | Blocked function patterns (regex) |
| `parse_limits` | `ParseLimits` | `DEFAULT_PARSE_LIMITS` | Parser safety limits |
| `operator_registry` | `OperatorRegistry` | `DEFAULT_OPERATOR_REGISTRY` | Custom operators |
| `custom_predicates` | `Mapping[str,CustomPredicateDefinition]` | `{}` | ORM-neutral predicates |
| `value_converter_registry` | `ValueConverterRegistry` | `DEFAULT_*` | Type converters |
| `field_value_converters` | `Mapping[str,ValueConverter]` | `{}` | Per-field-path converters |
| `model_field_value_converters` | `Mapping[type,Mapping[str,ValueConverter]]` | `{}` | Per-model converters |
| `json_options` | `JSONOptions` | `DEFAULT_JSON_OPTIONS` | JSON/JSONB behavior |

## SortOptions

Configuration fields for `Sort.parse(...)`:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `field_mapping` | `Mapping[str,str]` | `{}` | Global field aliases |
| `model_field_mapping` | `Mapping[type,Mapping[str,str]]` | `{}` | Per-model aliases |
| `join_hints` | `Mapping[str,JoinHint]` | `{}` | Relationship join hints |
| `field_whitelist` | `frozenset[str]` | `frozenset()` | Allowed field paths |
| `field_blacklist` | `frozenset[str]` | `frozenset()` | Blocked field paths |
| `model_field_whitelist` | `Mapping[type,frozenset[str]]` | `{}` | Per-model allowed fields |
| `model_field_blacklist` | `Mapping[type,frozenset[str]]` | `{}` | Per-model blocked fields |
| `procedure_whitelist` | `tuple[str,...]` | `()` | Allowed function patterns (regex) |
| `procedure_blacklist` | `tuple[str,...]` | `()` | Blocked function patterns (regex) |
| `sort_limits` | `SortLimits` | `DEFAULT_SORT_LIMITS` | Sort parser limits |
| `json_options` | `JSONOptions` | `DEFAULT_JSON_OPTIONS` | JSON/JSONB behavior |

## JSON Options & Types

### JSONOptions

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `use_datetime` | `bool` | `False` | Enable `.datetime()` in jsonpath |
| `path_exists_function` | `str` | `"jsonb_path_exists"` | PostgreSQL function name |
| `path_exists_tz_function` | `str` | `"jsonb_path_exists_tz"` | TZ-aware function name |
| `sort_field_types` | `Mapping[str,JSONSortScalarType]` | `{}` | Per-field sort scalar type |

### JSONSortScalarType

`TEXT`, `INTEGER`, `FLOAT`, `NUMERIC`, `BOOLEAN`, `DATE`, `TIME`,
`DATETIME`, `DATETIME_TZ`.

### JSONPath

`JSONPath(segments=("user", "id"))` - represents a dotted JSON path.
Methods: `to_dot_path()`, `to_postgresql_jsonpath()`, `is_root`.

### JSONPathComparison

`JSONPathComparison.from_raw_arguments(path, operator_name, raw_arguments)` -
builds a JSON path comparison from raw RSQL arguments.

### JSONScalarNormalizer / JSONScalarValue

Normalizes raw RSQL arguments into JSON-aware typed values.

### DEFAULT_JSON_OPTIONS

Shared immutable `JSONOptions()` instance used as default.

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
- explicit JSON sort typing via `JSONOptions.sort_field_types`

Not currently supported:

- non-SQLAlchemy ORMs

### JSON filter semantics

Current PostgreSQL JSON behavior is split into two modes:

- whole-document JSON comparison:
  - direct JSONB comparison
  - operators: `==`, `!=`, `=in=`, `=out=`, `=na=`, `=nn=`
- nested JSON path comparison:
  - PostgreSQL `jsonpath`
  - `JSONPATH`-typed binds
  - vars payload for structured values

### JSON sort semantics

Nested JSON sort defaults to text semantics unless explicitly configured.

`JSONOptions.sort_field_types` accepts:

- `JSONSortScalarType.TEXT`
- `JSONSortScalarType.INTEGER`
- `JSONSortScalarType.FLOAT`
- `JSONSortScalarType.NUMERIC`
- `JSONSortScalarType.BOOLEAN`
- `JSONSortScalarType.DATE`
- `JSONSortScalarType.TIME`
- `JSONSortScalarType.DATETIME`
- `JSONSortScalarType.DATETIME_TZ`

Whole-document JSON sort:

- is rejected by default
- is allowed only with explicit `TEXT` configuration
- does not currently support non-text semantics

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
- `filter_openapi_examples`
- `sort_openapi_examples`
- `page_openapi_examples`
- `size_openapi_examples`

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

### FastAPI adapter error payload

The adapter raises `HTTPException(status_code=422, detail=...)` with:

- `parameter`
- `error_type`
- `message`
- `details`

Each `details` item carries:

- `code`
- `message`
- `field`

Current error categories include:

- `query_parse_error`
- `query_semantic_error`
- `sort_parse_error`
- `sort_semantic_error`
- page-related validation errors

## FastAPI + SQLAlchemy Integration

`pyrsql.integrations.fastapi` exports:

- `FastAPISQLAlchemyIntegration`
- `FastAPISQLAlchemyResource`
- `SQLAlchemyPaginatedSelect`

`pyrsql.integrations.fastapi.sqlalchemy` exports the same public names.

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
- `resource(model, ...)`
- `base_select(model)`

### FastAPISQLAlchemyResource

Constructor-owned state:

- `integration`
- `model`
- `criteria_config`

Supported resource configuration through `integration.resource(...)`:

- `filterable_fields`
- `sortable_fields`
- `default_sort`
- `statement_factory`
- `max_page_size`
- custom query parameter names
- explicit filter and sort OpenAPI examples

Methods:

- `criteria_dependency()`
- `select(criteria)`
- `count_select(criteria)`
- `paginated_select(criteria)`
- `applier(criteria)`
- `select_dependency()`
- `count_select_dependency()`
- `paginated_select_dependency()`
- `applier_dependency()`

Notes:

- `default_sort` accepts forms like `-created_at` and `+name`
- `statement_factory` must return a SQLAlchemy `Select`
- `statement_factory` must return a `Select` compatible with the resource model
- `statement_factory` is invoked per use and is not cached

### SQLAlchemyPaginatedSelect

Carries:

- `statement`
- `count_statement`

## Core query objects

### Query

Carries:

- `text`
- `expression`
- `bound_expression`

### Sort

Carries:

- `text`
- `fields`
- `bound_sort`

### PageRequest

Carries:

- `page_number`
- `page_size`
- `bound_page`
