"""Small shared validation helpers."""

from __future__ import annotations


def validate_positive_int(value: int, *, field_name: str) -> None:
    """Validates one strictly positive integer field.

    Raises:
        TypeError: If the value is not an integer.
        ValueError: If the value is not greater than zero.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer.")
    if value <= 0:
        raise ValueError(f"{field_name} must be greater than 0.")
