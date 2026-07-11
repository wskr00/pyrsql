"""Shared Python-type inference helpers for SQLAlchemy ORM translation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.sql.elements import ColumnElement

_KNOWN_FUNCTION_RETURN_TYPES = {
    "lower": str,
    "upper": str,
    "concat": str,
}


def infer_sql_function_python_type(
    function_name: str,
    argument_types: tuple[type[Any] | None, ...],
    *,
    function_expression: ColumnElement[Any] | None = None,
) -> type[Any] | None:
    """Infers the Python type for one SQL function expression.

    This helper first asks SQLAlchemy for the concrete expression type when an
    expression is available, then falls back to cheap, explicit heuristics for
    a small set of well-known functions.

    Returns:
        The inferred Python type, or ``None`` when unknown.
    """
    if function_expression is not None:
        try:
            return function_expression.type.python_type
        except (AttributeError, NotImplementedError):
            pass
    normalized_name = function_name.lower()
    known_return_type = _KNOWN_FUNCTION_RETURN_TYPES.get(normalized_name)
    if known_return_type is not None:
        return known_return_type
    if normalized_name == "coalesce":
        for argument_type in argument_types:
            if argument_type is not None:
                return argument_type
    return None


def is_string_python_type(python_type: type[Any] | None) -> bool:
    """Returns whether the resolved Python type is string-compatible.

    Returns:
        ``True`` when the type is string-compatible.
    """
    if python_type is None:
        return False
    return issubclass(python_type, str)
