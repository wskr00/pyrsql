# Operators

## Comparison operators

| Operator | Aliases | Arity | Description |
|----------|---------|-------|-------------|
| `==` | | 1 | Equal |
| `!=` | | 1 | Not equal |
| `=gt=` | `>` | 1 | Greater than |
| `=ge=` | `>=` | 1 | Greater or equal |
| `=lt=` | `<` | 1 | Less than |
| `=le=` | `<=` | 1 | Less or equal |
| `=in=` | | 1..100 | IN (comma-separated args) |
| `=out=` | | 1..100 | NOT IN |
| `=like=` | | 1 | LIKE (supports `*` wildcard) |
| `=notlike=` | | 1 | NOT LIKE |
| `=ic=` | `=ilike=` | 1 | ILIKE (case-insensitive LIKE) |
| `=inotlike=` | | 1 | NOT ILIKE |
| `=bt=` | | 2 | BETWEEN (exactly 2 args) |
| `=nb=` | | 2 | NOT BETWEEN |
| `=na=` | | 0 | IS NULL |
| `=nn=` | | 0 | IS NOT NULL |

## Logical operators

| Operator | Aliases | Description |
|----------|---------|-------------|
| `;` | `and` | AND (higher precedence) |
| `,` | `or` | OR (lower precedence) |

## Sort modifiers

| Modifier | Example | Description |
|----------|---------|-------------|
| `asc` | `name,asc` | Ascending (default) |
| `desc` | `name,desc` | Descending |
| `ic` | `name,desc,ic` | Ignore case |
