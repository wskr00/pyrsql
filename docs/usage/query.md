# Filter Queries

## Basic comparisons

```python
from pyrsql import Query

Query.parse("name==demo")          # equal
Query.parse("name!=demo")          # not equal
Query.parse("age=gt=18")           # greater than
Query.parse("age=ge=18")           # greater or equal
Query.parse("age=lt=65")           # less than
Query.parse("age=le=65")           # less or equal
Query.parse("age>18")              # greater than (symbol)
Query.parse("age>=18")             # greater or equal (symbol)
Query.parse("age<65")              # less than (symbol)
Query.parse("age<=65")             # less or equal (symbol)
```

## Membership and null checks

```python
Query.parse("id=in=(1,2,3)")       # IN
Query.parse("id=out=(4,5)")        # NOT IN
Query.parse("name=na=")            # IS NULL
Query.parse("name=nn=")            # IS NOT NULL
```

## Text matching

```python
Query.parse("name=like=demo*")     # LIKE
Query.parse("name=notlike=demo")   # NOT LIKE
Query.parse("name=ic=demo*")       # ILIKE (case-insensitive)
Query.parse("name=ilike=DEMO")     # ILIKE alias
```

## Range

```python
Query.parse("score=bt=(10,20)")    # BETWEEN 10 AND 20
Query.parse("score=nb=(10,20)")    # NOT BETWEEN
```

## Logical composition

```python
Query.parse("name==demo;age=gt=18")       # AND (semicolon)
Query.parse("name==demo,age=gt=18")       # OR (comma)
Query.parse("(name==demo;age=gt=18),status==active")  # grouping
```

## Quoting

```python
Query.parse("name=='de\\'mo'")     # quoted string with escape
Query.parse("name=='*not a wildcard*'")  # literal asterisks inside quotes
```

## Wildcard matching in equality

By default, `*` in equality expressions is treated as a `LIKE` wildcard:

```python
Query.parse("name==*demo*")        # becomes LIKE '%demo%'
```

Disable with strict mode:

```python
Query.parse("name=='*demo*'", options=QueryOptions(strict_equality=True))
```

## Case-insensitive equality

```python
Query.parse("name==^demo")         # case-insensitive via LOWER()
```

## LIKE escape character

```python
Query.parse("name=like='$%'", options=QueryOptions(like_escape_character="$"))
```

## DISTINCT

```python
Query.parse("company.name==demo", options=QueryOptions(distinct=True))
```

## Function selectors

Whitelist SQL functions to use in filter expressions:

```python
Query.parse(
    "@upper[name]==DEMO",
    options=QueryOptions(procedure_whitelist=("upper",)),
)
```

## Parser limits

```python
from pyrsql.parsing.limits import ParseLimits

Query.parse("...", options=QueryOptions(
    parse_limits=ParseLimits(
        max_query_length=4096,
        max_expression_depth=8,
        max_node_count=512,
    ),
))
```

## Package-level helper

```python
import pyrsql

query = pyrsql.parse("name==demo")                     # parse only
result = pyrsql.compile("name==demo", orm=my_orm)       # parse + compile
applied = pyrsql.apply(target, Model, "name==demo", orm=my_orm)  # full cycle
```
