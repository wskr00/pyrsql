# Value Conversion

## Built-in type converters

`bool`, `int`, `float`, `Decimal`, `UUID`, `date`, `time`, `datetime`,
`enum` members (by name or value), and `dict`/`list` from JSON strings.

## Custom converter registration

```python
from pyrsql import ValueConverterRegistry

registry = ValueConverterRegistry({}).with_converter(str, lambda raw: raw.upper())
```

## Field-scoped converters

```python
from pyrsql import QueryOptions

options = QueryOptions(
    field_value_converters={
        "created_at": lambda raw: datetime.strptime(raw, "%d/%m/%Y"),
    },
)
```

## Model-scoped converters

```python
options = QueryOptions(
    model_field_value_converters={
        User: {"status": lambda raw: Status[raw.upper()]},
    },
)
```

## Custom converter registry

```python
options = QueryOptions(
    value_converter_registry=ValueConverterRegistry({str: my_converter}),
)
```
