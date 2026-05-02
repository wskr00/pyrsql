"""Unit tests for orm-neutral value conversion."""

import datetime as dt
from decimal import Decimal
from enum import Enum
from uuid import UUID

import pytest

from pyrsql.core.conversion import DEFAULT_VALUE_CONVERTER_REGISTRY
from pyrsql.core.conversion import ValueConversionError
from pyrsql.core.conversion import ValueConverterRegistry


class Status(Enum):
    """Example enum for value conversion tests."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class CustomIdentifier:
    """Simple constructor-based conversion target."""

    def __init__(self, value: str) -> None:
        self.value = value


def test_default_registry_converts_common_scalar_types() -> None:
    """Converts bool, int, float, decimal and UUID values."""
    assert DEFAULT_VALUE_CONVERTER_REGISTRY.convert("true", bool) is True
    assert DEFAULT_VALUE_CONVERTER_REGISTRY.convert("10", int) == 10
    assert DEFAULT_VALUE_CONVERTER_REGISTRY.convert("2.5", float) == 2.5
    assert DEFAULT_VALUE_CONVERTER_REGISTRY.convert("3.14", Decimal) == (
        Decimal("3.14")
    )
    assert DEFAULT_VALUE_CONVERTER_REGISTRY.convert(
        "12345678-1234-5678-1234-567812345678",
        UUID,
    ) == UUID("12345678-1234-5678-1234-567812345678")


def test_default_registry_converts_iso_date_and_time_types() -> None:
    """Converts ISO date, time and datetime values."""
    assert DEFAULT_VALUE_CONVERTER_REGISTRY.convert(
        "2026-05-02",
        dt.date,
    ) == dt.date(2026, 5, 2)
    assert DEFAULT_VALUE_CONVERTER_REGISTRY.convert(
        "10:15:30",
        dt.time,
    ) == dt.time(10, 15, 30)
    assert DEFAULT_VALUE_CONVERTER_REGISTRY.convert(
        "2026-05-02T10:15:30",
        dt.datetime,
    ) == dt.datetime(2026, 5, 2, 10, 15, 30)


def test_default_registry_falls_back_from_date_to_datetime() -> None:
    """Converts ISO dates into midnight datetimes when needed."""
    assert DEFAULT_VALUE_CONVERTER_REGISTRY.convert(
        "2026-05-02",
        dt.datetime,
    ) == dt.datetime(2026, 5, 2, 0, 0)


def test_default_registry_converts_enums() -> None:
    """Converts enums by name first, then by enum value."""
    assert DEFAULT_VALUE_CONVERTER_REGISTRY.convert(
        "ACTIVE",
        Status,
    ) is Status.ACTIVE
    assert DEFAULT_VALUE_CONVERTER_REGISTRY.convert(
        "inactive",
        Status,
    ) is Status.INACTIVE


def test_default_registry_uses_string_constructor_fallback() -> None:
    """Falls back to plain constructor-based conversion."""
    converted = DEFAULT_VALUE_CONVERTER_REGISTRY.convert(
        "abc-123",
        CustomIdentifier,
    )
    assert isinstance(converted, CustomIdentifier)
    assert converted.value == "abc-123"


def test_registry_supports_custom_converter_registration() -> None:
    """Extends the registry immutably with custom converters."""
    registry = ValueConverterRegistry({}).with_converter(
        str,
        lambda raw: raw.upper(),
    )
    assert registry.convert("demo", str) == "DEMO"


def test_registry_raises_value_conversion_error() -> None:
    """Raises a typed error for invalid conversions."""
    with pytest.raises(ValueConversionError):
        DEFAULT_VALUE_CONVERTER_REGISTRY.convert("invalid", bool)
