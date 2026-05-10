# Field Mapping & Access Control

## Global field aliases

```python
from pyrsql import QueryOptions, Query

options = QueryOptions(field_mapping={"username": "user.name"})
query = Query.parse("username==demo", options=options)
```

## Global whitelist / blacklist

```python
options = QueryOptions(
    field_whitelist=frozenset({"name", "email"}),
    field_blacklist=frozenset({"password"}),
)
```

## Per-model policies

```python
options = QueryOptions(
    model_field_mapping={User: {"companyName": "name"}},
    model_field_whitelist={User: frozenset({"name", "email"})},
    model_field_blacklist={Admin: frozenset({"internal_notes"})},
)
```

## Procedure (function) policies

Procedure whitelist/blacklist use regex patterns:

```python
options = QueryOptions(
    procedure_whitelist=("upper", "concat|lower"),
    procedure_blacklist=("dangerous_.*",),
)
```

`"concat|lower"` matches both `concat` and `lower`. `"dangerous_.*"` blocks
any function starting with `dangerous_`.

Policies apply to both filter queries (`@upper[name]==DEMO`) and sort
expressions (`@upper[name],asc`).
