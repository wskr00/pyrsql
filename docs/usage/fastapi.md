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

When parsing or semantic binding fails, the adapter raises `HTTPException(422)`
with a structured payload:

```json
{
  "detail": {
    "parameter": "filter",
    "type": "query_parse_error",
    "errors": [
      {
        "code": "parse_error",
        "message": "...",
        "location": {"index": 4, "line": 1, "column": 5}
      }
    ]
  }
}
```

Error types: `query_parse_error`, `query_semantic_error`, `sort_parse_error`,
`sort_semantic_error`, page validation errors.
