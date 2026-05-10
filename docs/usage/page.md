# Pagination

## Page-number based

```python
from pyrsql import PageRequest

page = PageRequest.of(2, 25)       # page 2, 25 items/page -> offset 50
page = PageRequest.of(0, 10)       # first page
```

## Offset based

```python
page = PageRequest.from_offset(offset=20, limit=10)  # page 2, 10 items/page
```

## Applying to a statement

```python
stmt = page.apply(stmt, User, orm=orm)
```

## Page-level properties

```python
page.page_number   # 0-based
page.page_size     # items per page
page.offset        # computed offset
page.limit         # alias for page_size
```
