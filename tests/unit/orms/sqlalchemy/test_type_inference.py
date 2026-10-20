"""Unit tests for SQLAlchemy expression type inference."""

from __future__ import annotations

from sqlalchemy import func

from pyrsql.orms.sqlalchemy.type_inference import infer_sql_function_python_type


def test_known_function_type_precedes_generic_sqlalchemy_type() -> None:
    """Uses the known return type when SQLAlchemy reports ``object``."""
    assert (
        infer_sql_function_python_type(
            "upper",
            (str,),
            function_expression=func.upper("name"),
        )
        is str
    )


def test_unknown_sqlalchemy_object_type_remains_untyped() -> None:
    """Treats SQLAlchemy's generic ``object`` type as unavailable."""
    assert (
        infer_sql_function_python_type(
            "custom_function",
            (),
            function_expression=func.custom_function("name"),
        )
        is None
    )


def test_coalesce_uses_argument_type() -> None:
    """Uses the first known argument type for ``coalesce``."""
    assert (
        infer_sql_function_python_type(
            "coalesce",
            (None, str),
            function_expression=func.coalesce(None, "name"),
        )
        is str
    )
