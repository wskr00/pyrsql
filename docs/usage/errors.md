# Error Handling

This page explains the main error categories exposed by `pyrsql`, what they
mean, and how they surface in FastAPI integrations.

## Core error categories

### Parse errors

Parse errors mean the input string is not valid query or sort syntax.

Examples:

- malformed filter expressions
- malformed sort expressions
- invalid grouping or operator shape

Relevant classes:

- `pyrsql.parsing.errors.ParseError`
- `pyrsql.parsing.errors.LexError`
- `pyrsql.sorting.errors.SortParseError`

### Semantic errors

Semantic errors mean the syntax is valid, but the requested operation is not
allowed or cannot be resolved under the current rules.

Examples:

- field blocked by whitelist or blacklist
- function blocked by whitelist or blacklist
- invalid selector meaning after parsing succeeds

Relevant classes:

- `pyrsql.semantic.errors.SemanticError`
- `pyrsql.semantic.errors.FieldNotWhitelistedError`
- `pyrsql.semantic.errors.FieldBlacklistedError`
- `pyrsql.semantic.errors.FunctionNotWhitelistedError`
- `pyrsql.semantic.errors.FunctionBlacklistedError`
- `pyrsql.sorting.errors.SortFieldNotWhitelistedError`
- `pyrsql.sorting.errors.SortFieldBlacklistedError`
- `pyrsql.sorting.errors.SortFunctionNotWhitelistedError`
- `pyrsql.sorting.errors.SortFunctionBlacklistedError`

### Page validation errors

Page validation errors come from the FastAPI adapter when request pagination
parameters are invalid or inconsistent.

Examples:

- page number below the allowed minimum
- missing page size when one is required
- invalid `one_based_paging` request values

These are exposed through the FastAPI adapter payload model, not through a
dedicated core exception hierarchy.

### Backend errors

Backend errors happen after parsing and semantic binding, when a backend cannot
lower or resolve a valid request against the target ORM/model.

Examples:

- unmapped SQLAlchemy path
- model inspection failure
- unsupported JSON lowering case

Relevant classes:

- `pyrsql.orms.base.ORMError`
- `pyrsql.orms.sqlalchemy.errors.SQLAlchemyORMError`
- `pyrsql.orms.sqlalchemy.errors.SQLAlchemyModelInspectionError`
- `pyrsql.orms.sqlalchemy.errors.SQLAlchemyPathResolutionError`
- `pyrsql.orms.sqlalchemy.errors.SQLAlchemyJSONSupportError`

## FastAPI status codes

When you use the FastAPI adapter or FastAPI + SQLAlchemy integration, error
categories map to HTTP status codes like this:

| Category | Status |
|----------|--------|
| Query parse errors | `400` |
| Sort parse errors | `400` |
| Page validation/configuration errors | `400` |
| Query semantic errors | `422` |
| Sort semantic errors | `422` |
| Backend integration errors | `422` |

In practice:

- `400` means the request shape itself is invalid
- `422` means the request is syntactically valid but cannot be accepted or
  lowered under current rules

## FastAPI payload shape

FastAPI responses are normalized through
`FastAPIAdapterErrorPayload`.

Typical payload shape:

```json
{
  "detail": {
    "type": "urn:pyrsql:problem:query-parse-error",
    "title": "Query parse error",
    "parameter": "filter",
    "detail": "Expected selector after operator.",
    "errors": [
      {
        "code": "parse_error",
        "detail": "Expected selector after operator.",
        "field": null,
        "location": {
          "index": 4,
          "line": 1,
          "column": 5
        }
      }
    ]
  }
}
```

Top-level fields:

- `type`: stable problem URI
- `title`: human-readable problem category
- `parameter`: request parameter involved (`filter`, `sort`, `page`, `size`)
- `detail`: summary text
- `errors`: one or more structured detail items

Detail fields:

- `code`: stable machine-readable error code
- `detail`: normalized message
- `field`: optional field or selector name when available
- `location`: optional source location for parse/semantic issues

## Interpreting common cases

### `query_parse_error`

The filter string could not be parsed.

Typical causes:

- incomplete operator usage
- broken parentheses
- malformed argument lists

### `query_semantic_error`

The filter string parsed successfully, but the requested selector or function
was rejected by policy or semantic rules.

Typical causes:

- field not in whitelist
- field blocked by blacklist
- function not allowed

### `sort_parse_error`

The sort string is malformed.

Typical causes:

- missing direction separator
- malformed function selector
- invalid sort token order

### `sort_semantic_error`

The sort string parsed successfully, but the selected field or function is not
allowed.

### `query_backend_error` / `sort_backend_error`

The request survived parsing and semantic checks, but backend lowering failed.

Typical causes:

- unresolved SQLAlchemy field path
- unsupported model metadata shape
- unsupported JSON operation for the configured backend

## Debugging guidance

When debugging a failure, the most useful order is:

1. check the HTTP status category: `400` vs `422`
2. check the top-level `type`
3. inspect the first `errors[*].code`
4. inspect `field` and `location` when present

For backend errors, also verify:

- the model field path actually exists
- the route/integration is using the intended field policies
- the backend supports the requested JSON or function behavior

## Related pages

- [FastAPI Adapter](fastapi.md)
- [FastAPI + SQLAlchemy](fastapi-sqlalchemy.md)
- [Async Flows](async.md)
- [API Reference](../reference/api.md)
