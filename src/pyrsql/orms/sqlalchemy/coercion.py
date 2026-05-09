"""SQLAlchemy ORM value coercion."""

from typing import Any

from pyrsql.core.conversion import (
    FieldValueConverterSet,
    ValueConversionError,
    ValueConverterRegistry,
)
from pyrsql.orms.sqlalchemy.errors import SQLAlchemyORMError


class SQLAlchemyValueCoercer:
    """Coerces bound argument values using resolved Python types."""

    def __init__(
        self,
        *,
        registry: ValueConverterRegistry | None = None,
    ) -> None:
        self._registry = registry

    def coerce(
        self,
        raw_value: str,
        python_type: type[Any] | None,
        *,
        field_converter_set: FieldValueConverterSet | None = None,
        model: type[Any] | None = None,
        field_name: str | None = None,
        field_path: str | None = None,
        registry: ValueConverterRegistry | None = None,
    ) -> Any:
        """Coerces a raw argument into a typed Python value."""
        if field_converter_set is not None:
            field_converter = field_converter_set.resolve(
                model=model,
                field_name=field_name,
                field_path=field_path,
            )
            if field_converter is not None:
                try:
                    return field_converter(raw_value)
                except Exception as error:
                    raise SQLAlchemyORMError(
                        f"Failed to convert {raw_value!r} for field "
                        f"{field_path or field_name!r}."
                    ) from error
        active_registry = registry or self._registry
        if active_registry is None:
            raise SQLAlchemyORMError(
                "SQLAlchemyValueCoercer requires a conversion registry."
            )
        try:
            return active_registry.convert(raw_value, python_type)
        except ValueConversionError as error:
            raise SQLAlchemyORMError(str(error)) from error
