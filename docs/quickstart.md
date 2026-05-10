# Quickstart

## Install

```bash
pip install pyrsql                    # core only
pip install pyrsql[sqlalchemy]        # with SQLAlchemy
pip install pyrsql[fastapi]           # with FastAPI
pip install pyrsql[fastapi,sqlalchemy]  # both
```

## Filter

```python
from pyrsql import Query

Query.parse("name==demo")            # equal
Query.parse("age=gt=18")             # greater than
Query.parse("id=in=(1,2,3)")         # IN
Query.parse("name=like=demo*")       # LIKE
Query.parse("score=bt=(10,20)")      # BETWEEN
Query.parse("name==demo;age=gt=18")  # AND
Query.parse("name==demo,age=gt=18")  # OR
```

## Sort

```python
from pyrsql import Sort

Sort.parse("name")              # ascending
Sort.parse("name,desc")         # descending
Sort.parse("name,asc;company.name,desc")  # multi-field
```

## Paginate

```python
from pyrsql import PageRequest

PageRequest.of(0, 25)   # first page, 25 items
PageRequest.of(2, 25)   # third page, 25 items
```

## SQLAlchemy

```python
from pyrsql.orms.sqlalchemy import SQLAlchemyORM
from sqlalchemy import select

orm = SQLAlchemyORM()

# Apply to a SQLAlchemy Select
stmt = Query.parse("name==demo").apply(select(User), User, orm=orm)
```

## FastAPI

```python
from fastapi import Depends, FastAPI
from pyrsql.adapters.fastapi import RequestCriteria, criteria_dependency

app = FastAPI()

@app.get("/items")
def list_items(criteria = Depends(criteria_dependency())):
    ...
```

Query params `filter`, `sort`, `page`, `size` are extracted automatically.
Parse and semantic errors become `HTTP 422` with structured diagnostics.
