# Sort

## Basic sort

```python
from pyrsql import Sort

Sort.parse("name")                 # ascending (default)
Sort.parse("name,asc")             # explicit ascending
Sort.parse("name,desc")            # descending
```

## Multi-field

```python
Sort.parse("name,asc;company.name,desc")
```

## Ignore case

```python
Sort.parse("name,desc,ic")         # case-insensitive descending
```

## Function selectors

```python
Sort.parse(
    "@upper[name],asc",
    options=SortOptions(procedure_whitelist=("upper",)),
)
```

## Sort limits

```python
from pyrsql.sorting.limits import SortLimits

Sort.parse("...", options=SortOptions(
    sort_limits=SortLimits(max_fields=5, max_sort_length=256),
))
```
