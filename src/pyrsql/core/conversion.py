"""Backend-neutral value conversion support."""

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from types import MappingProxyType
from typing import Any
from typing import Mapping
from uuid import UUID


ValueConverter = Callable[[str], Any]


class ValueConversionError(ValueError):
    """Raised when a raw RSQL value cannot be converted."""


def _convert_bool(raw_value: str) -> bool:
    """Converts a string to bool using explicit accepted values."""
    lowered = raw_value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    raise ValueConversionError(f"Cannot convert {raw_value!r} to bool.")


@dataclass(frozen=True, slots=True)
class ValueConverterRegistry:
    """Immutable registry of backend-neutral string-to-type converters."""

    converters: Mapping[type[Any], ValueConverter]

    def __post_init__(self) -> None:
        """Normalizes the converter mapping into an immutable view."""
        object.__setattr__(
            self,
            "converters",
            MappingProxyType(dict(self.converters)),
        )

    def with_converter(
        self,
        target_type: type[Any],
        converter: ValueConverter,
    ) -> "ValueConverterRegistry":
        """Returns a new registry with one additional converter."""
        updated = dict(self.converters)
        updated[target_type] = converter
        return ValueConverterRegistry(updated)

    def convert(
        self,
        raw_value: str,
        target_type: type[Any] | None,
    ) -> Any:
        """Converts a raw string into the requested target type."""
        if target_type is None:
            return raw_value

        if target_type is dt.datetime:
            return self._convert_datetime(raw_value)

        converter = self._find_registered_converter(target_type)
        if converter is not None:
            try:
                return converter(raw_value)
            except Exception as error:  # pragma: no cover - defensive wrap
                raise ValueConversionError(
                    f"Failed to convert {raw_value!r} to "
                    f"{target_type.__name__}."
                ) from error

        try:
            if issubclass(target_type, Enum):
                return self._convert_enum(raw_value, target_type)
            if issubclass(target_type, str):
                return raw_value
        except TypeError as error:  # pragma: no cover - invalid type object
            raise ValueConversionError(
                f"Unsupported target type {target_type!r}."
            ) from error

        return self._construct_from_string(raw_value, target_type)

    def _find_registered_converter(
        self,
        target_type: type[Any],
    ) -> ValueConverter | None:
        """Finds the most specific registered converter for a type."""
        for candidate in target_type.__mro__:
            converter = self.converters.get(candidate)
            if converter is not None:
                return converter
        return None

    def _convert_enum(
        self,
        raw_value: str,
        target_type: type[Any],
    ) -> Any:
        """Converts a string into an enum member by name first."""
        try:
            return target_type[raw_value]
        except KeyError:
            try:
                return target_type(raw_value)
            except ValueError as error:
                raise ValueConversionError(
                    f"Failed to convert {raw_value!r} to "
                    f"{target_type.__name__}."
                ) from error

    def _convert_datetime(self, raw_value: str) -> dt.datetime:
        """Converts a string into datetime with LocalDate-style fallback."""
        try:
            return dt.datetime.fromisoformat(raw_value)
        except ValueError as error:
            try:
                parsed_date = dt.date.fromisoformat(raw_value)
            except ValueError as date_error:
                raise ValueConversionError(
                    f"Failed to convert {raw_value!r} to datetime."
                ) from date_error
            parsed_datetime = dt.datetime.combine(parsed_date, dt.time.min)
            if parsed_datetime is None:  # pragma: no cover
                raise ValueConversionError(
                    f"Failed to convert {raw_value!r} to datetime."
                ) from error
            return parsed_datetime

    def _construct_from_string(
        self,
        raw_value: str,
        target_type: type[Any],
    ) -> Any:
        """Attempts a plain constructor-based conversion as a fallback."""
        try:
            return target_type(raw_value)
        except Exception as error:
            raise ValueConversionError(
                f"Failed to convert {raw_value!r} to "
                f"{target_type.__name__}."
            ) from error


DEFAULT_VALUE_CONVERTER_REGISTRY = ValueConverterRegistry(
    {
        bool: _convert_bool,
        int: int,
        float: float,
        Decimal: Decimal,
        UUID: UUID,
        dt.date: dt.date.fromisoformat,
        dt.time: dt.time.fromisoformat,
    }
)
