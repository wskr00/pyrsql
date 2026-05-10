# Custom Predicates

Define custom operators with ORM-specific lowering.

## Define the operator

```python
from pyrsql import CustomPredicateDefinition, QueryOptions
from pyrsql.parsing.operators import ComparisonOperator

all_match = ComparisonOperator(
    name="all_match",
    spellings=("=all=",),
    minimum_arguments=1,
    maximum_arguments=1,
)
```

## Register with QueryOptions

```python
options = QueryOptions(
    custom_predicates={
        "all_match": CustomPredicateDefinition(
            operator=all_match,
            argument_type=str,
        ),
    },
)
query = Query.parse("name=all=demo", options=options)
```

## ORM-specific lowering (SQLAlchemy)

```python
from pyrsql.orms.sqlalchemy import SQLAlchemyORM
from sqlalchemy import func

orm = SQLAlchemyORM(
    custom_predicates={
        "all_match": lambda payload: (
            func.lower(payload.expression) == str(payload.values[0]).lower()
        ),
    },
)
```

The `payload` object provides:

- `payload.expression` - the resolved SQLAlchemy column
- `payload.values` - converted argument values
- `payload.field_path` - the resolved field path
- `payload.options` - the QueryOptions in use
