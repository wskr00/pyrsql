"""ORM-neutral JSON options."""

import re
from collections.abc import Mapping
from enum import Enum
from types import MappingProxyType

import msgspec

_SQL_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class JSONSortScalarType(str, Enum):
    """Supported scalar cast strategies for JSON sort expressions."""

    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    NUMERIC = "numeric"
    BOOLEAN = "boolean"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    DATETIME_TZ = "datetime_tz"


class JSONOptions(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """ORM-neutral JSON behavior flags.

    Attributes:
        path_exists_function: SQL function used for JSON path existence.
        path_exists_tz_function: SQL function used for timezone-aware JSON path
            existence checks.
        use_datetime: Whether JSON values should be interpreted as datetimes
            when possible.
    """

    path_exists_function: str = "jsonb_path_exists"
    path_exists_tz_function: str = "jsonb_path_exists_tz"
    use_datetime: bool = False
    sort_field_types: Mapping[str, JSONSortScalarType] = MappingProxyType({})

    def __post_init__(self) -> None:
        """Validates configured SQL function names.

        Raises:
            ValueError: If either configured SQL function name is empty.
        """
        self._validate_sql_identifier(
            self.path_exists_function,
            field_name="path_exists_function",
        )
        self._validate_sql_identifier(
            self.path_exists_tz_function,
            field_name="path_exists_tz_function",
        )
        if not isinstance(self.sort_field_types, Mapping):
            raise TypeError("sort_field_types must be a mapping.")
        object.__setattr__(
            self,
            "sort_field_types",
            MappingProxyType(
                {
                    self._normalize_sort_field_path(path): (
                        sort_type
                        if isinstance(sort_type, JSONSortScalarType)
                        else JSONSortScalarType(sort_type)
                    )
                    for path, sort_type in self.sort_field_types.items()
                }
            ),
        )

    @staticmethod
    def _validate_sql_identifier(value: str, *, field_name: str) -> None:
        """Validates one SQL function identifier."""
        if not value:
            raise ValueError(f"{field_name} cannot be empty.")
        if value != value.strip():
            raise ValueError(
                f"{field_name} must not contain outer whitespace."
            )
        if _SQL_IDENTIFIER_PATTERN.fullmatch(value) is None:
            raise ValueError(
                f"{field_name} must be a valid SQL identifier."
            )

    @staticmethod
    def _normalize_sort_field_path(path: str) -> str:
        """Validates one configured JSON sort field path."""
        if not path:
            raise ValueError("JSON sort field paths cannot be empty.")
        if path != path.strip():
            raise ValueError(
                "JSON sort field paths must not contain outer whitespace."
            )
        return path


DEFAULT_JSON_OPTIONS = JSONOptions()
