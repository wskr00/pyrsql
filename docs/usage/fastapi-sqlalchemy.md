# FastAPI + SQLAlchemy Integration

## Setup

```python
from pyrsql.integrations.fastapi import FastAPISQLAlchemyIntegration

integration = FastAPISQLAlchemyIntegration()
```

## Dependency factories

```python
@app.get("/users")
def list_users(
    stmt: Annotated[Any, Depends(integration.select_dependency(User))],
):
    return {"sql": str(stmt.compile(compile_kwargs={"literal_binds": True}))}

@app.get("/users/count")
def count_users(
    stmt: Annotated[Any, Depends(integration.count_select_dependency(User))],
):
    ...

@app.get("/users/paginated")
def paginated_users(
    bundle: Annotated[Any, Depends(integration.paginated_select_dependency(User))],
):
    # bundle.statement -> the filtered + sorted + paged SELECT
    # bundle.count_statement -> the filtered count SELECT
    ...
```

## Declarative resources

```python
users = integration.resource(
    User,
    filterable_fields={"id", "name"},
    sortable_fields={"name"},
    default_sort="name,desc",
    max_page_size=50,
    filter_examples={"by_name": {"summary": "By name", "value": "name==demo"}},
)

@app.get("/users")
def list_users(stmt: Annotated[Any, Depends(users.select_dependency())]):
    ...
```

Resources auto-generate OpenAPI examples for filterable and sortable fields.

Also available: `count_select_dependency()`, `paginated_select_dependency()`,
`applier_dependency()`.

## Custom base statement

```python
users = integration.resource(
    User,
    statement_factory=lambda: select(User).where(User.status == "active"),
    default_sort="-name",
)
```

## Applying criteria directly

```python
stmt = integration.apply(select(User), User, request_criteria)
stmt = integration.select(User, request_criteria)
stmt = integration.count_select(User, request_criteria)
bundle = integration.paginated_select(User, request_criteria)
```

## Custom ORM configuration

```python
from pyrsql.adapters.fastapi import FastAPICriteriaConfig

integration = FastAPISQLAlchemyIntegration(
    orm=SQLAlchemyORM(...),
    criteria_config=FastAPICriteriaConfig(default_page_size=20),
)
```
