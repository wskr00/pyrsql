"""Unit tests for ORM-neutral value conversion."""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
from decimal import Decimal
from enum import Enum
from uuid import UUID

import pytest

from pyrsql.core.conversion import (
    DEFAULT_VALUE_CONVERTER_REGISTRY,
    FieldValueConverterSet,
    ValueConversionError,
    ValueConverterRegistry,
)


class Status(Enum):
    """Example enum for value conversion tests."""

    ACTIVE = "active"
    INACTIVE = "inactive"


@dataclass
class CustomIdentifier:
    """Simple constructor-based conversion target."""

    value: str


class StringList(list[str]):  # noqa: FURB189
    """List subclass used to verify container rewrapping."""


class StringMap(dict[str, str]):  # noqa: FURB189
    """Dict subclass used to verify container rewrapping."""


@pytest.mark.parametrize(
    ("raw_value", "target_type", "expected"),
    [
        pytest.param("true", bool, True, id="bool"),
        pytest.param("10", int, 10, id="int"),
        pytest.param("2.5", float, 2.5, id="float"),
        pytest.param("3.14", Decimal, Decimal("3.14"), id="decimal"),
        pytest.param(
            "12345678-1234-5678-1234-567812345678",
            UUID,
            UUID("12345678-1234-5678-1234-567812345678"),
            id="uuid",
        ),
        pytest.param(
            "2026-05-02",
            dt.date,
            dt.date(2026, 5, 2),
            id="date",
        ),
        pytest.param(
            "10:15:30",
            dt.time,
            dt.time(10, 15, 30),
            id="time",
        ),
        pytest.param(
            "2026-05-02T10:15:30",
            dt.datetime,
            dt.datetime(2026, 5, 2, 10, 15, 30),  # noqa: DTZ001
            id="datetime",
        ),
        pytest.param(
            "2026-05-02T10:15:30Z",
            dt.datetime,
            dt.datetime(2026, 5, 2, 10, 15, 30, tzinfo=dt.timezone.utc),
            id="datetime-utc",
        ),
    ],
)
def test_default_registry_converts_registered_scalar_types(
    raw_value: str,
    target_type: type[object],
    expected: object,
) -> None:
    """Converts built-in scalar and temporal target types."""
    assert (
        DEFAULT_VALUE_CONVERTER_REGISTRY.convert(raw_value, target_type)
        == expected
    )


def test_default_registry_falls_back_from_date_to_datetime() -> None:
    """Converts ISO dates into midnight datetimes when needed."""
    assert DEFAULT_VALUE_CONVERTER_REGISTRY.convert(
        "2026-05-02",
        dt.datetime,
    ) == dt.datetime(2026, 5, 2, 0, 0)  # noqa: DTZ001


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        pytest.param("ACTIVE", Status.ACTIVE, id="enum-name"),
        pytest.param("inactive", Status.INACTIVE, id="enum-value"),
    ],
)
def test_default_registry_converts_enums(
    raw_value: str,
    expected: Status,
) -> None:
    """Converts enums by member name first, then by value."""
    assert (
        DEFAULT_VALUE_CONVERTER_REGISTRY.convert(raw_value, Status) is expected
    )


def test_default_registry_uses_string_constructor_fallback() -> None:
    """Falls back to constructor-based conversion for custom types."""
    converted = DEFAULT_VALUE_CONVERTER_REGISTRY.convert(
        "abc-123",
        CustomIdentifier,
    )

    assert isinstance(converted, CustomIdentifier)
    assert converted.value == "abc-123"


@pytest.mark.parametrize(
    ("raw_value", "target_type", "expected"),
    [
        pytest.param(
            '{"kind":"demo","count":2}',
            dict,
            {"kind": "demo", "count": 2},
            id="dict",
        ),
        pytest.param(
            '["a","b","c"]',
            list,
            ["a", "b", "c"],
            id="list",
        ),
    ],
)
def test_default_registry_converts_json_container_types(
    raw_value: str,
    target_type: type[object],
    expected: object,
) -> None:
    """Converts JSON container strings into native values."""
    assert (
        DEFAULT_VALUE_CONVERTER_REGISTRY.convert(raw_value, target_type)
        == expected
    )


@pytest.mark.parametrize(
    ("raw_value", "target_type", "expected_type"),
    [
        pytest.param(
            '["a","b","c"]',
            StringList,
            StringList,
            id="list-subclass",
        ),
        pytest.param(
            '{"kind":"demo","count":"2"}',
            StringMap,
            StringMap,
            id="dict-subclass",
        ),
    ],
)
def test_default_registry_rewraps_json_container_subclasses(
    raw_value: str,
    target_type: type[object],
    expected_type: type[object],
) -> None:
    """Rewraps decoded builtin JSON containers into requested subclasses."""
    converted = DEFAULT_VALUE_CONVERTER_REGISTRY.convert(raw_value, target_type)

    assert isinstance(converted, expected_type)


@pytest.mark.parametrize(
    ("raw_value", "target_type"),
    [
        pytest.param('["a","b"]', dict, id="list-to-dict"),
        pytest.param('{"a":1}', list, id="dict-to-list"),
        pytest.param("{invalid", dict, id="invalid-json-dict"),
        pytest.param("invalid", bool, id="invalid-bool"),
        pytest.param("2026-13-02", dt.date, id="invalid-date"),
        pytest.param("25:15:30", dt.time, id="invalid-time"),
        pytest.param("2026-99-02T10:15:30", dt.datetime, id="invalid-datetime"),
    ],
)
def test_default_registry_raises_typed_errors_for_invalid_conversion(
    raw_value: str,
    target_type: type[object],
) -> None:
    """Raises ValueConversionError for unsupported input shapes and values."""
    with pytest.raises(ValueConversionError):
        DEFAULT_VALUE_CONVERTER_REGISTRY.convert(raw_value, target_type)


def test_registry_supports_custom_converter_registration() -> None:
    """Extends the registry immutably with custom converters."""

    def _to_upper(raw: str) -> str:
        return raw.upper()

    registry = ValueConverterRegistry({}).with_converter(str, _to_upper)

    assert registry.convert("demo", str) == "DEMO"


def test_registry_wraps_non_domain_errors_from_custom_converters() -> None:
    """Normalizes unexpected custom converter failures into domain errors."""

    def _broken_converter(raw: str) -> str:
        raise RuntimeError(raw)

    registry = ValueConverterRegistry({str: _broken_converter})

    with pytest.raises(ValueConversionError, match="Failed to convert 'demo'"):
        registry.convert("demo", str)


class ExampleModel:
    """Simple model marker used for field-converter resolution tests."""


def test_field_value_converter_set_prefers_model_specific_converter() -> None:
    """Resolves model-scoped converters before global field-path converters."""
    converters = FieldValueConverterSet(
        field_converters={"payload.value": lambda raw: raw.upper()},
        model_field_converters={
            ExampleModel: {"value": lambda raw: raw.lower()},
        },
    )

    resolved = converters.resolve(
        model=ExampleModel,
        field_name="value",
        field_path="payload.value",
    )

    assert resolved is not None
    assert resolved("MiXeD") == "mixed"
