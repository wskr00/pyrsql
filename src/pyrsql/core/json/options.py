"""ORM-neutral JSON options."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class JSONOptions:
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
        if not self.path_exists_function:
            raise ValueError("path_exists_function cannot be empty.")
        if not self.path_exists_tz_function:
            raise ValueError("path_exists_tz_function cannot be empty.")
