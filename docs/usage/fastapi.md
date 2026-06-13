# FastAPI Adapter

## Basic usage

```python
from typing import Annotated
from fastapi import Depends, FastAPI
from pyrsql.adapters.fastapi import RequestCriteria, criteria_dependency

app = FastAPI()
dependency = criteria_dependency()

@app.get("/items")
def list_items(criteria: Annotated[RequestCriteria, Depends(dependency)]):
    return {"is_empty": criteria.is_empty}
```

The adapter extracts `filter`, `sort`, `page`, and `size` from query
parameters and builds a `RequestCriteria`.

The dependency itself does not need to be `async`. It is compatible with both
sync and async FastAPI routes because it only parses request data and builds
criteria objects.

## Configuration

```python
from pyrsql.adapters.fastapi import FastAPICriteriaConfig

config = FastAPICriteriaConfig(
    filter_parameter="where",        # custom query param names
    sort_parameter="order",
    page_parameter="p",
    size_parameter="per_page",
    default_page_size=25,
    max_page_size=100,
    one_based_paging=True,           # page numbers start at 1
    query_options=QueryOptions(strict_equality=True),
)
dependency = criteria_dependency(config)
```

## Class-based dependency

```python
from pyrsql.adapters.fastapi import CriteriaDependency

dependency = CriteriaDependency(FastAPICriteriaConfig(default_page_size=15))

@app.get("/items")
def list_items(criteria: Annotated[RequestCriteria, Depends(dependency)]):
    ...
```

## OpenAPI examples

```python
config = FastAPICriteriaConfig(
    filter_openapi_examples={
        "by_name": {"summary": "Filter by name", "value": "name==demo"},
    },
    sort_openapi_examples={
        "newest": {"summary": "Newest first", "value": "created_at,desc"},
    },
)
```

## Error handling

The adapter distinguishes between request-shape errors and semantic policy
errors:

- `400` for parse failures and page validation/configuration failures
- `422` for semantic query/sort failures

Example parse failure payload:

```json
{
  "detail": {
    "parameter": "filter",
    "type": "urn:pyrsql:problem:query-parse-error",
    "errors": [
      {
        "code": "parse_error",
        "detail": "...",
        "location": {"index": 4, "line": 1, "column": 5}
      }
    ]
  }
}
```

Error types: `query_parse_error`, `query_semantic_error`, `sort_parse_error`,
`sort_semantic_error`, page validation errors.

When used together with the SQLAlchemy integration layer, backend ORM failures
such as unmapped fields are also translated into structured `HTTP 422`
responses instead of bubbling up as raw `500` errors.

## Async compatibility

The adapter dependency itself does not perform I/O. It is safe to use in both:

- synchronous FastAPI routes
- `async def` FastAPI routes

If you also use SQLAlchemy async execution, see [Async Flows](async.md).
