"""ORM-neutral JSON options."""

import re

import msgspec

_SQL_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


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


DEFAULT_JSON_OPTIONS = JSONOptions()
