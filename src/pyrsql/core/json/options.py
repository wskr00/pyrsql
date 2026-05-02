"""Backend-neutral JSON options."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class JSONOptions:
    """Backend-neutral JSON behavior flags."""

    use_datetime: bool = False
