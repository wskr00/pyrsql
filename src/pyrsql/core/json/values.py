"""ORM-neutral JSON value normalization."""

from __future__ import annotations

import re
from typing import TypeAlias, cast

import msgspec

_INTEGER_PATTERN = re.compile(r"^-?\d+$")
_FLOAT_PATTERN = re.compile(
    r"^-?(?:\d+\.\d+|\d+(?:\.\d+)?[eE][+-]?\d+)$",
)

JSONValue: TypeAlias = (
    bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"] | None
)
_JSON_ENCODER = msgspec.json.Encoder()
_JSON_DECODER = msgspec.json.Decoder()


class JSONScalarValue(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Represents one normalized JSON scalar or structured value."""

    value: JSONValue
    json_literal: str
    python_type: type[object] | None


class JSONScalarNormalizer:
    """Normalizes raw RSQL arguments to JSON-aware values."""

    def normalize(
        self,
        raw_value: str,
        *,
        quoted: bool,
    ) -> JSONScalarValue:
        """Builds one JSON value from a raw RSQL argument.

        Returns:
            One normalized JSON scalar or structured value.
        """
        if quoted:
            parsed_json = self._try_parse_json(raw_value)
            if parsed_json is not None:
                return self._from_python_value(parsed_json)
            return self._from_python_value(raw_value)

        match raw_value.lower():
            case "true":
                return self._from_python_value(value=True)
            case "false":
                return self._from_python_value(value=False)
            case "null":
                return self._from_python_value(value=None)
            case _:
                pass
        if _INTEGER_PATTERN.fullmatch(raw_value):
            parsed_integer = self._try_parse_json_number(raw_value)
            if parsed_integer is not None:
                return self._from_python_value(parsed_integer)
        if _FLOAT_PATTERN.fullmatch(raw_value):
            parsed_float = self._try_parse_json_number(raw_value)
            if parsed_float is not None:
                return self._from_python_value(parsed_float)
        return self._from_python_value(raw_value)

    @staticmethod
    def _from_python_value(value: JSONValue) -> JSONScalarValue:
        """Creates a normalized JSON value from a Python object.

        Returns:
            One normalized JSON value wrapper.
        """
        return JSONScalarValue(
            value=value,
            json_literal=_JSON_ENCODER.encode(value).decode("utf-8"),
            python_type=type(value) if value is not None else None,
        )

    @staticmethod
    def _try_parse_json(raw_value: str) -> JSONValue | None:
        """Parses quoted JSON arguments when they contain containers.

        Returns:
            The parsed JSON value, or ``None`` when the argument should remain
            a plain string.
        """
        try:
            parsed = cast("JSONValue", _JSON_DECODER.decode(raw_value))
        except msgspec.DecodeError:
            return None
        if not isinstance(parsed, dict | list):
            return None
        return parsed

    @staticmethod
    def _try_parse_json_number(raw_value: str) -> int | float | None:
        """Parses one unquoted JSON number using JSON number semantics.

        Returns:
            The parsed numeric value, or ``None`` when the number is invalid.
        """
        try:
            parsed = _JSON_DECODER.decode(raw_value)
        except msgspec.DecodeError:
            return None
        if isinstance(parsed, bool) or not isinstance(parsed, int | float):
            return None
        return parsed


DEFAULT_JSON_SCALAR_NORMALIZER = JSONScalarNormalizer()
