"""Unit tests for SQLAlchemy ORM value coercion."""

import pytest

from pyrsql.core.conversion import (
    DEFAULT_VALUE_CONVERTER_REGISTRY,
    FieldValueConverterSet,
)
from pyrsql.orms.sqlalchemy.coercion import SQLAlchemyValueCoercer
from pyrsql.orms.sqlalchemy.errors import SQLAlchemyORMError


class ExampleModel:
    """Simple model marker used for field-scoped coercion tests."""


def test_value_coercer_uses_registry_for_json_container_types() -> None:
    """Coerces JSON strings through the shared registry."""
    coercer = SQLAlchemyValueCoercer(
        registry=DEFAULT_VALUE_CONVERTER_REGISTRY
    )

    converted = coercer.coerce('["rg","cpf"]', list)

    assert converted == ["rg", "cpf"]


def test_value_coercer_uses_field_specific_converter_first() -> None:
    """Prefers field-scoped converters over the generic registry."""
    coercer = SQLAlchemyValueCoercer(
        registry=DEFAULT_VALUE_CONVERTER_REGISTRY
    )
    field_converters = FieldValueConverterSet(
        field_converters={"context.aliases": lambda raw: raw.upper()},
        model_field_converters={},
    )

    converted = coercer.coerce(
        "cpf",
        str,
        field_converter_set=field_converters,
        field_path="context.aliases",
    )

    assert converted == "CPF"


def test_value_coercer_wraps_field_converter_errors() -> None:
    """Raises ORM errors with field context for field-scoped failures."""
    coercer = SQLAlchemyValueCoercer(
        registry=DEFAULT_VALUE_CONVERTER_REGISTRY
    )
    field_converters = FieldValueConverterSet(
        field_converters={},
        model_field_converters={ExampleModel: {"aliases": int}},
    )

    with pytest.raises(
        SQLAlchemyORMError,
        match="Failed to convert 'abc' for field 'aliases'\\.",
    ):
        coercer.coerce(
            "abc",
            int,
            field_converter_set=field_converters,
            model=ExampleModel,
            field_name="aliases",
        )


def test_value_coercer_requires_a_registry() -> None:
    """Rejects coercion when no conversion registry is available."""
    coercer = SQLAlchemyValueCoercer()

    with pytest.raises(
        SQLAlchemyORMError,
        match="requires a conversion registry",
    ):
        coercer.coerce("demo", str)
