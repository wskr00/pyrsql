"""SQLAlchemy ORM value coercion."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyrsql.core.conversion import (
    ValueConversionError,
)
from pyrsql.orms.sqlalchemy.errors import SQLAlchemyORMError

if TYPE_CHECKING:
    from pyrsql.core.conversion import (
        FieldValueConverterSet,
        ValueConverter,
        ValueConverterRegistry,
    )


class SQLAlchemyValueCoercer:
    """Coerces bound argument values using resolved Python types."""

    __slots__ = ("_registry",)

    def __init__(
        self,
        *,
        registry: ValueConverterRegistry | None = None,
    ) -> None:
        """Initializes the coercer with an optional conversion registry."""
        self._registry = registry

    def coerce(
        self,
        raw_value: str,
        python_type: type[object] | None,
        *,
        field_converter_set: FieldValueConverterSet | None = None,
        model: type[object] | None = None,
        field_name: str | None = None,
        field_path: str | None = None,
        registry: ValueConverterRegistry | None = None,
    ) -> object:
        """Coerces a raw argument into a typed Python value.

        Returns:
            The coerced Python value.
        """
        field_converter = None
        if field_converter_set is not None:
            field_converter = field_converter_set.resolve(
                model=model,
                field_name=field_name,
                field_path=field_path,
            )
        if field_converter is not None:
            return self._coerce_with_field_converter(
                raw_value,
                field_converter,
                field_label=field_path or field_name,
            )
        return self._coerce_with_registry(
            raw_value,
            python_type,
            registry=registry,
        )

    @staticmethod
    def _coerce_with_field_converter(
        raw_value: str,
        field_converter: ValueConverter,
        *,
        field_label: str | None,
    ) -> object:
        """Coerces one value using a resolved field-specific converter.

        Returns:
            The coerced Python value.

        Raises:
            SQLAlchemyORMError: If the field-specific conversion fails.
        """
        try:
            return field_converter(raw_value)
        except Exception as error:
            raise SQLAlchemyORMError(
                f"Failed to convert {raw_value!r} for field {field_label!r}.",
            ) from error

    def _coerce_with_registry(
        self,
        raw_value: str,
        python_type: type[object] | None,
        *,
        registry: ValueConverterRegistry | None,
    ) -> object:
        """Coerces one value using the active conversion registry.

        Returns:
            The coerced Python value.

        Raises:
            SQLAlchemyORMError: If no registry is available or conversion
                fails.
        """
        active_registry = registry or self._registry
        if active_registry is None:
            raise SQLAlchemyORMError(
                "SQLAlchemyValueCoercer requires a conversion registry.",
            )
        try:
            return active_registry.convert(raw_value, python_type)
        except ValueConversionError as error:
            raise SQLAlchemyORMError(str(error)) from error
