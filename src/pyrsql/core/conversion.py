"""ORM-neutral value conversion support."""

from __future__ import annotations

from collections.abc import Callable
import datetime as dt
from decimal import Decimal
from enum import Enum
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, TypeAlias
from uuid import UUID

import msgspec

if TYPE_CHECKING:
    from collections.abc import Mapping

_JSON_DICT_DECODER = msgspec.json.Decoder(type=dict)
_JSON_LIST_DECODER = msgspec.json.Decoder(type=list)

RawValue: TypeAlias = str
ConvertedValue: TypeAlias = Any
TargetType: TypeAlias = type[Any]
ValueConverter: TypeAlias = Callable[[RawValue], ConvertedValue]


class ValueConversionError(ValueError):
    """Raised when a raw RSQL value cannot be converted."""


def _build_conversion_error(
    raw_value: RawValue,
    target_type: TargetType,
    *,
    cause: Exception | None = None,
) -> ValueConversionError:
    """Builds one normalized conversion error instance.

    Returns:
        A normalized value conversion error.
    """
    error = ValueConversionError(
        f"Failed to convert {raw_value!r} to {target_type.__name__}.",
    )
    if cause is not None:
        error.__cause__ = cause
    return error


def _convert_bool(raw_value: RawValue) -> bool:
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


def _convert_datetime(raw_value: RawValue) -> dt.datetime:
    """Converts a string into datetime with LocalDate-style fallback.

    Returns:
        The converted datetime value.

    Raises:
        _build_conversion_error: If the input cannot be parsed as datetime or
            ISO date.
    """
    try:
        return msgspec.convert(
            raw_value,
            type=dt.datetime,
            strict=False,
        )
    except msgspec.ValidationError:
        pass
    try:
        parsed_date = dt.date.fromisoformat(raw_value)
    except ValueError as date_error:
        raise _build_conversion_error(
            raw_value,
            dt.datetime,
            cause=date_error,
        ) from date_error
    return dt.datetime.combine(parsed_date, dt.time.min)


def _build_msgspec_converter(
    target_type: TargetType,
) -> ValueConverter:
    """Builds one msgspec-backed scalar converter.

    Returns:
        A converter that validates and coerces a string via ``msgspec``.
    """

    def converter(raw_value: RawValue) -> ConvertedValue:
        try:
            return msgspec.convert(
                raw_value,
                type=target_type,
                strict=False,
            )
        except msgspec.ValidationError as error:
            raise _build_conversion_error(
                raw_value,
                target_type,
                cause=error,
            ) from error

    return converter


class ValueConverterRegistry(msgspec.Struct, frozen=True, gc=False):
    """Immutable registry of orm-neutral string-to-type converters."""

    converters: Mapping[TargetType, ValueConverter]

    def __post_init__(self) -> None:
        """Normalizes the converter mapping into an immutable view."""
        msgspec.structs.force_setattr(
            self,
            "converters",
            MappingProxyType(dict(self.converters)),
        )

    def with_converter(
        self,
        target_type: TargetType,
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
        raw_value: RawValue,
        target_type: TargetType | None,
    ) -> ConvertedValue:
        """Converts a raw string into the requested target type.

        Returns:
            The converted value, or the raw string when no target type is
            provided.
        """
        if target_type is None:
            return raw_value

        converter = self._find_registered_converter(target_type)
        if converter is not None:
            return self._convert_with_registered_converter(
                raw_value,
                target_type,
                converter,
            )
        return self._convert_without_registered_converter(
            raw_value,
            target_type,
        )

    def _find_registered_converter(
        self,
        target_type: TargetType,
    ) -> ValueConverter | None:
        """Finds the most specific registered converter for a type.

        Returns:
            The most specific registered converter, or ``None``.
        """
        direct_converter = self.converters.get(target_type)
        if direct_converter is not None:
            return direct_converter
        for candidate in target_type.__mro__:
            if candidate is target_type:
                continue
            converter = self.converters.get(candidate)
            if converter is not None:
                return converter
        return None

    @staticmethod
    def _convert_with_registered_converter(
        raw_value: RawValue,
        target_type: TargetType,
        converter: ValueConverter,
    ) -> ConvertedValue:
        """Converts one value through a registered converter.

        Returns:
            The converted value from the registered converter.

        Raises:
            ValueConversionError: If the converter fails.
            _build_conversion_error: If the converter raises an unexpected
                exception.
        """
        try:
            return converter(raw_value)
        except ValueConversionError:
            raise
        except Exception as error:  # pragma: no cover - defensive wrap
            raise _build_conversion_error(
                raw_value,
                target_type,
                cause=error,
            ) from error

    def _convert_without_registered_converter(
        self,
        raw_value: RawValue,
        target_type: TargetType,
    ) -> ConvertedValue:
        """Converts one value through built-in fallback strategies.

        Returns:
            The converted value from built-in fallback strategies.

        Raises:
            ValueConversionError: If conversion fails or the type is invalid.
        """
        try:
            if issubclass(target_type, Enum):
                return self._convert_enum(raw_value, target_type)
            if issubclass(target_type, str):
                return raw_value
            if issubclass(target_type, dict) or issubclass(target_type, list):
                return self._convert_json_container(raw_value, target_type)
        except TypeError as error:  # pragma: no cover - invalid type object
            raise ValueConversionError(
                f"Unsupported target type {target_type!r}.",
            ) from error
        return self._construct_from_string(raw_value, target_type)

    @staticmethod
    def _convert_enum(
        raw_value: RawValue,
        target_type: TargetType,
    ) -> ConvertedValue:
        """Converts a string into an enum member by name first.

        Returns:
            The resolved enum member.

        Raises:
            _build_conversion_error: If no enum member matches the raw value.
        """
        try:
            return target_type[raw_value]
        except KeyError:
            try:
                return target_type(raw_value)
            except ValueError as error:
                raise _build_conversion_error(
                    raw_value,
                    target_type,
                    cause=error,
                ) from error

    @staticmethod
    def _construct_from_string(
        raw_value: RawValue,
        target_type: TargetType,
    ) -> ConvertedValue:
        """Attempts a plain constructor-based conversion as a fallback.

        Returns:
            The converted value produced by the target type constructor.

        Raises:
            _build_conversion_error: If the target type constructor fails.
        """
        try:
            return target_type(raw_value)
        except Exception as error:
            raise _build_conversion_error(
                raw_value,
                target_type,
                cause=error,
            ) from error

    @staticmethod
    def _convert_json_container(
        raw_value: RawValue,
        target_type: TargetType,
    ) -> ConvertedValue:
        """Converts a JSON string into a mapping or sequence container.

        Returns:
            The converted mapping or sequence value.

        Raises:
            ValueConversionError: If the target type is not a supported JSON
                container type.
            _build_conversion_error: If decoding or rewrapping fails.
        """
        expected_type: TargetType
        if issubclass(target_type, dict):
            expected_type = dict
            decoder = _JSON_DICT_DECODER
        elif issubclass(target_type, list):
            expected_type = list
            decoder = _JSON_LIST_DECODER
        else:  # pragma: no cover - guarded by convert()
            raise ValueConversionError(
                f"Unsupported target type {target_type!r}.",
            )

        try:
            decoded = decoder.decode(raw_value)
        except (msgspec.DecodeError, msgspec.ValidationError) as error:
            raise _build_conversion_error(
                raw_value,
                target_type,
                cause=error,
            ) from error

        if target_type is expected_type:
            return decoded
        try:
            return target_type(decoded)
        except Exception as error:
            raise _build_conversion_error(
                raw_value,
                target_type,
                cause=error,
            ) from error


class FieldValueConverterSet(msgspec.Struct, frozen=True, gc=False):
    """Immutable field-scoped value converter configuration."""

    field_converters: Mapping[str, ValueConverter]
    model_field_converters: Mapping[type[Any], Mapping[str, ValueConverter]]

    def __post_init__(self) -> None:
        """Normalizes nested converter mappings into immutable views."""
        msgspec.structs.force_setattr(
            self,
            "field_converters",
            MappingProxyType(dict(self.field_converters)),
        )
        msgspec.structs.force_setattr(
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
        model: type[Any] | None,
        field_name: str | None,
        field_path: str | None,
    ) -> ValueConverter | None:
        """Resolves the most specific converter configured for a field.

        Returns:
            The most specific configured converter, or ``None``.

        Resolution precedence:
            1. model-scoped converter by ``model`` + ``field_name``
            2. global field-path converter by ``field_path``
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
        int: _build_msgspec_converter(int),
        float: _build_msgspec_converter(float),
        Decimal: _build_msgspec_converter(Decimal),
        UUID: _build_msgspec_converter(UUID),
        dt.date: _build_msgspec_converter(dt.date),
        dt.time: _build_msgspec_converter(dt.time),
        dt.datetime: _convert_datetime,
    },
)

DEFAULT_FIELD_VALUE_CONVERTER_SET = FieldValueConverterSet(
    field_converters={},
    model_field_converters={},
)
