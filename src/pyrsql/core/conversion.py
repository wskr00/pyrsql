"""ORM-neutral value conversion support."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import datetime as dt
from decimal import Decimal
from enum import Enum
from types import MappingProxyType
from typing import TYPE_CHECKING
from uuid import UUID

import ciso8601
import msgspec

if TYPE_CHECKING:
    from collections.abc import Mapping

ValueConverter = Callable[[str], object]


class ValueConversionError(ValueError):
    """Raised when a raw RSQL value cannot be converted."""


def _convert_bool(raw_value: str) -> bool:
    """Converts a string to bool using explicit accepted values.

    Returns:
        The converted boolean value.

    Raises:
        ValueConversionError: If the input is not an accepted boolean literal.
    """
    match raw_value.lower():
        case "true":
            return True
        case "false":
            return False
        case _:
            raise ValueConversionError(
                f"Cannot convert {raw_value!r} to bool.",
            )


def _convert_datetime(raw_value: str) -> dt.datetime:
    """Converts a string into datetime with LocalDate-style fallback.

    Returns:
        The converted datetime value.

    Raises:
        ValueConversionError: If the input cannot be parsed as datetime or
            ISO date.
    """
    try:
        parsed_datetime = ciso8601.parse_datetime(raw_value)
    except ValueError:
        parsed_datetime = None
    if parsed_datetime is not None:
        return parsed_datetime
    try:
        parsed_date = dt.date.fromisoformat(raw_value)
    except ValueError as date_error:
        raise ValueConversionError(
            f"Failed to convert {raw_value!r} to datetime.",
        ) from date_error
    return dt.datetime.combine(parsed_date, dt.time.min)


@dataclass(frozen=True, slots=True)
class ValueConverterRegistry:
    """Immutable registry of orm-neutral string-to-type converters."""

    converters: Mapping[type[object], ValueConverter]

    def __post_init__(self) -> None:
        """Normalizes the converter mapping into an immutable view."""
        object.__setattr__(
            self,
            "converters",
            MappingProxyType(dict(self.converters)),
        )

    def with_converter(
        self,
        target_type: type[object],
        converter: ValueConverter,
    ) -> ValueConverterRegistry:
        """Returns a new registry with one additional converter.

        Returns:
            A new registry containing the additional converter.
        """
        updated = dict(self.converters)
        updated[target_type] = converter
        return ValueConverterRegistry(updated)

    def convert(
        self,
        raw_value: str,
        target_type: type[object] | None,
    ) -> object:
        """Converts a raw string into the requested target type.

        Returns:
            The converted value, or the raw string when no target type is
            provided.

        Raises:
            ValueConversionError: If conversion fails or the target type is
                unsupported.
        """
        if target_type is None:
            return raw_value

        converter = self._find_registered_converter(target_type)
        if converter is not None:
            try:
                return converter(raw_value)
            except Exception as error:  # pragma: no cover - defensive wrap
                raise ValueConversionError(
                    f"Failed to convert {raw_value!r} to "
                    f"{target_type.__name__}.",
                ) from error

        try:
            if issubclass(target_type, Enum):
                return self._convert_enum(raw_value, target_type)
            if issubclass(target_type, str):
                return raw_value
            if issubclass(target_type, dict):
                return self._convert_json_container(raw_value, target_type)
            if issubclass(target_type, list):
                return self._convert_json_container(raw_value, target_type)
        except TypeError as error:  # pragma: no cover - invalid type object
            raise ValueConversionError(
                f"Unsupported target type {target_type!r}.",
            ) from error

        return self._construct_from_string(raw_value, target_type)

    def _find_registered_converter(
        self,
        target_type: type[object],
    ) -> ValueConverter | None:
        """Finds the most specific registered converter for a type.

        Returns:
            The most specific registered converter, or ``None``.
        """
        for candidate in target_type.__mro__:
            converter = self.converters.get(candidate)
            if converter is not None:
                return converter
        return None

    @staticmethod
    def _convert_enum(
        raw_value: str,
        target_type: type[object],
    ) -> object:
        """Converts a string into an enum member by name first.

        Returns:
            The resolved enum member.

        Raises:
            ValueConversionError: If no enum member matches the raw value.
        """
        try:
            return target_type[raw_value]
        except KeyError:
            try:
                return target_type(raw_value)
            except ValueError as error:
                raise ValueConversionError(
                    f"Failed to convert {raw_value!r} to "
                    f"{target_type.__name__}.",
                ) from error

    @staticmethod
    def _construct_from_string(
        raw_value: str,
        target_type: type[object],
    ) -> object:
        """Attempts a plain constructor-based conversion as a fallback.

        Returns:
            The converted value produced by the target type constructor.

        Raises:
            ValueConversionError: If the target type constructor fails.
        """
        try:
            return target_type(raw_value)
        except Exception as error:
            raise ValueConversionError(
                f"Failed to convert {raw_value!r} to {target_type.__name__}.",
            ) from error

    @staticmethod
    def _convert_json_container(
        raw_value: str,
        target_type: type[object],
    ) -> object:
        """Converts a JSON string into a mapping or sequence container.

        Returns:
            The converted mapping or sequence value.

        Raises:
            ValueConversionError: If the JSON payload is invalid, has the wrong
                container shape, or cannot be rewrapped into the target type.
        """
        try:
            decoded = msgspec.json.decode(raw_value)
        except msgspec.DecodeError as error:
            raise ValueConversionError(
                f"Failed to convert {raw_value!r} to {target_type.__name__}.",
            ) from error

        expected_type: type[object]
        if issubclass(target_type, dict):
            expected_type = dict
        elif issubclass(target_type, list):
            expected_type = list
        else:  # pragma: no cover - guarded by convert()
            raise ValueConversionError(
                f"Unsupported target type {target_type!r}.",
            )

        if not isinstance(decoded, expected_type):
            raise ValueConversionError(
                f"Failed to convert {raw_value!r} to {target_type.__name__}.",
            )
        if target_type is expected_type:
            return decoded
        try:
            return target_type(decoded)
        except Exception as error:
            raise ValueConversionError(
                f"Failed to convert {raw_value!r} to {target_type.__name__}.",
            ) from error


@dataclass(frozen=True, slots=True)
class FieldValueConverterSet:
    """Immutable field-scoped value converter configuration."""

    field_converters: Mapping[str, ValueConverter]
    model_field_converters: Mapping[type[object], Mapping[str, ValueConverter]]

    def __post_init__(self) -> None:
        """Normalizes nested converter mappings into immutable views."""
        object.__setattr__(
            self,
            "field_converters",
            MappingProxyType(dict(self.field_converters)),
        )
        object.__setattr__(
            self,
            "model_field_converters",
            MappingProxyType(
                {
                    model: MappingProxyType(dict(converters))
                    for model, converters in self.model_field_converters.items()
                },
            ),
        )

    def resolve(
        self,
        *,
        model: type[object] | None,
        field_name: str | None,
        field_path: str | None,
    ) -> ValueConverter | None:
        """Resolves the most specific converter configured for a field.

        Returns:
            The most specific configured converter, or ``None``.
        """
        if model is not None and field_name is not None:
            model_converters = self.model_field_converters.get(model)
            if model_converters is not None:
                converter = model_converters.get(field_name)
                if converter is not None:
                    return converter
        if field_path is not None:
            return self.field_converters.get(field_path)
        return None


DEFAULT_VALUE_CONVERTER_REGISTRY = ValueConverterRegistry(
    {
        bool: _convert_bool,
        int: int,
        float: float,
        Decimal: Decimal,
        UUID: UUID,
        dt.date: dt.date.fromisoformat,
        dt.time: dt.time.fromisoformat,
        dt.datetime: _convert_datetime,
    },
)

DEFAULT_FIELD_VALUE_CONVERTER_SET = FieldValueConverterSet(
    field_converters={},
    model_field_converters={},
)
