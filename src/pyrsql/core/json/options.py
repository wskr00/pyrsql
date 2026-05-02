"""ORM-neutral JSON options."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class JSONOptions:
    """ORM-neutral JSON behavior flags."""

    path_exists_function: str = "jsonb_path_exists"
    path_exists_tz_function: str = "jsonb_path_exists_tz"
    use_datetime: bool = False

    def __post_init__(self) -> None:
        """Validates configured SQL function names."""
        if not self.path_exists_function:
            raise ValueError("path_exists_function cannot be empty.")
        if not self.path_exists_tz_function:
            raise ValueError("path_exists_tz_function cannot be empty.")
