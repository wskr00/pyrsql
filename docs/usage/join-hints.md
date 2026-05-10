# Join Hints

Control how relationships are joined:

```python
from pyrsql import QueryOptions
from pyrsql.core.joins import JoinHint

options = QueryOptions(join_hints={"User.company": JoinHint.LEFT})
```

Supported hints:

| Hint | Behavior |
|------|----------|
| `JoinHint.INNER` | `INNER JOIN` (default) |
| `JoinHint.LEFT` | `LEFT OUTER JOIN` |
| `JoinHint.RIGHT` | Rejected by SQLAlchemy backend |

Join hints apply to both queries and sorts.
