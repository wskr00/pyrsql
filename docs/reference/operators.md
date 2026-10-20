# Operators

Pyrsql supports the base RSQL comparison operators and the extensions used by
PerplexHub's JPA specification.

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
| `=like=` | `=ke=` | 1 | Contains match (`LIKE '%value%'`) |
| `=notlike=` | `=nk=` | 1 | Negated contains match |
| `=ilike=` | `=ik=` | 1 | Case-insensitive contains match |
| `=inotlike=` | `=ni=` | 1 | Negated case-insensitive contains match |
| `=ic=` | `=icase=` | 1 | Case-insensitive equality |
| `=bt=` | `=between=` | 2 | BETWEEN (exactly 2 args) |
| `=nb=` | `=notbetween=` | 2 | NOT BETWEEN (exactly 2 args) |
| `=na=` | `=isnull=`, `=null=` | 0..1 | IS NULL |
| `=nn=` | `=notnull=`, `=isnotnull=` | 0..1 | IS NOT NULL |

For `=like=`, `=notlike=`, `=ilike=`, and `=inotlike=`, pyrsql surrounds the
argument with `%` to match anywhere in the value. These operators use SQL
`LIKE` pattern rules: `%` matches any number of characters, `_` matches one,
and `*` is literal. The `like_escape_character` option controls SQL pattern
escaping.

For string-column `==` and `!=`, `*` is the wildcard and any `^` marker
requests case-insensitive matching. Quoting an argument does not disable these
markers. Use `=in=(*)` to match a literal asterisk.

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
