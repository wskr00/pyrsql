"""ORM-neutral JSON value normalization."""

from __future__ import annotations

import re
from typing import TypeAlias

import msgspec

_INTEGER_PATTERN = re.compile(r"^-?\d+$")
_FLOAT_PATTERN = re.compile(
    r"^-?(?:\d+\.\d+|\d+(?:\.\d+)?[eE][+-]?\d+)$",
)

JSONValue: TypeAlias = (
    bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"] | None
)


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
                return self._from_python_value(True)
            case "false":
                return self._from_python_value(False)
            case "null":
                return self._from_python_value(None)
            case _:
                pass
        if _INTEGER_PATTERN.fullmatch(raw_value):
            return self._from_python_value(int(raw_value))
        if _FLOAT_PATTERN.fullmatch(raw_value):
            return self._from_python_value(float(raw_value))
        return self._from_python_value(raw_value)

    @staticmethod
    def _from_python_value(value: JSONValue) -> JSONScalarValue:
        """Creates a normalized JSON value from a Python object.

        Returns:
            One normalized JSON value wrapper.
        """
        return JSONScalarValue(
            value=value,
            json_literal=msgspec.json.encode(value).decode("utf-8"),
            python_type=type(value) if value is not None else None,
        )

    @staticmethod
    def _try_parse_json(raw_value: str) -> JSONValue | None:
        """Parses quoted JSON arguments when they contain JSON values.

        Returns:
            The parsed JSON value, or ``None`` when the argument should remain
            a plain string.
        """
        try:
            parsed = msgspec.json.decode(raw_value)
        except msgspec.DecodeError:
            return None
        if isinstance(parsed, str):
            return None
        return parsed


DEFAULT_JSON_SCALAR_NORMALIZER = JSONScalarNormalizer()
