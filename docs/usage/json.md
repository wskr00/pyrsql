# JSON / JSONB

PostgreSQL JSON and JSONB columns are supported via two distinct query modes.

## Whole-document comparison

When the selector targets the JSON column directly, values are compared as
JSONB:

```python
from pyrsql import Query

Query.parse('payload=={"kind":"demo"}')     # JSON object equality
Query.parse('payload==["rg","cpf"]')         # JSON array equality
Query.parse("payload=na=")                   # IS NULL
Query.parse("payload=nn=")                   # IS NOT NULL
Query.parse("payload=in=([1,2],[3,4])")     # IN
```

Supported whole-document operators: `==`, `!=`, `=in=`, `=out=`, `=na=`, `=nn=`.

## Nested path comparison

Traversal into the JSON document uses PostgreSQL `jsonpath`:

```python
Query.parse("payload.user.id==1")
Query.parse("payload.user.name==demo")
Query.parse("payload.tags==[1,2]")
```

Arrays and objects are passed through `jsonpath` vars:

```python
Query.parse("payload.tags=='[1,2]'")         # quoted array -> vars payload
Query.parse("payload.meta=='{\"id\":1}'")    # quoted object -> vars payload
```

## Temporal JSON path semantics

```python
from pyrsql import JSONOptions, QueryOptions

query = Query.parse(
    "payload.created_at=gt=2026-05-01T10:30:00Z",
    options=QueryOptions(json_options=JSONOptions(use_datetime=True)),
)
```

With `use_datetime=True`, datetime values are rendered as `.datetime()` in
the `jsonpath` expression. For timezone-aware values, `jsonb_path_exists_tz`
is used.

## Custom JSON path function names

```python
options = QueryOptions(json_options=JSONOptions(
    path_exists_function="my_custom_json_path_exists",
    path_exists_tz_function="my_custom_json_path_exists_tz",
))
```

## JSON Sort

Nested JSON sort defaults to text semantics:

```python
from pyrsql import Sort

Sort.parse("payload.user.name,asc")
```

For typed JSON values, configure explicitly:

```python
from pyrsql import JSONOptions, JSONSortScalarType, SortOptions

Sort.parse("payload.user.id,asc", options=SortOptions(json_options=JSONOptions(
    sort_field_types={"payload.user.id": JSONSortScalarType.INTEGER},
)))
```

Supported scalar types: `TEXT`, `INTEGER`, `FLOAT`, `NUMERIC`, `BOOLEAN`,
`DATE`, `TIME`, `DATETIME`, `DATETIME_TZ`.

Whole-document JSON sort requires explicit `TEXT` configuration; other
whole-document sort types are rejected.
