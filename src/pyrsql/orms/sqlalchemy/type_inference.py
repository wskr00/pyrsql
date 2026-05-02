"""Shared Python-type inference helpers for SQLAlchemy ORM translation."""

from typing import Any

_STRING_SQL_FUNCTIONS = frozenset({"lower", "upper", "concat"})


def infer_sql_function_python_type(
    function_name: str,
    argument_types: tuple[type[Any] | None, ...],
) -> type[Any] | None:
    """Infers the Python type for common SQL functions."""
    normalized_name = function_name.lower()
    if normalized_name in _STRING_SQL_FUNCTIONS:
        return str
    if normalized_name == "coalesce":
        for argument_type in argument_types:
            if argument_type is not None:
                return argument_type
    return None


def is_string_python_type(python_type: type[Any] | None) -> bool:
    """Returns whether the resolved Python type is string-compatible."""
    if python_type is None:
        return False
    return issubclass(python_type, str)
