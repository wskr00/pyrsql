"""Backend-neutral JSON value normalization."""

import json
import re
from dataclasses import dataclass
from typing import Any

_INTEGER_PATTERN = re.compile(r"^-?\d+$")
_FLOAT_PATTERN = re.compile(r"^-?\d+\.\d+$")


@dataclass(frozen=True, slots=True)
class JSONScalarValue:
    """Represents one normalized JSON scalar or structured value."""

    value: Any
    json_literal: str
    python_type: type[Any] | None


class JSONScalarNormalizer:
    """Normalizes raw RSQL arguments to JSON-aware values."""

    def normalize(
        self,
        raw_value: str,
        *,
        quoted: bool,
    ) -> JSONScalarValue:
        """Builds one JSON value from a raw RSQL argument."""
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

    def _from_python_value(self, value: Any) -> JSONScalarValue:
        """Creates a normalized JSON value from a Python object."""
        return JSONScalarValue(
            value=value,
            json_literal=json.dumps(value),
            python_type=type(value) if value is not None else None,
        )

    def _try_parse_json(self, raw_value: str) -> Any | None:
        """Parses quoted JSON arguments when they contain JSON values."""
        try:
            parsed = json.loads(raw_value)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, str):
            return None
        return parsed


DEFAULT_JSON_SCALAR_NORMALIZER = JSONScalarNormalizer()
