"""SQLAlchemy backend value coercion."""

from typing import Any

from pyrsql.core.conversion import ValueConversionError
from pyrsql.core.conversion import ValueConverterRegistry
from pyrsql.backends.sqlalchemy.errors import SQLAlchemyBackendError


class SQLAlchemyValueCoercer:
    """Coerces semantic argument values using resolved Python types."""

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
        registry: ValueConverterRegistry | None = None,
    ) -> Any:
        """Coerces a raw argument into a typed Python value."""
        active_registry = registry or self._registry
        if active_registry is None:
            raise SQLAlchemyBackendError(
                "SQLAlchemyValueCoercer requires a conversion registry."
            )
        try:
            return active_registry.convert(raw_value, python_type)
        except ValueConversionError as error:
            raise SQLAlchemyBackendError(str(error)) from error
