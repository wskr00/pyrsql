"""Unit tests for SQLAlchemy ORM value coercion."""

from __future__ import annotations

import pytest

from pyrsql.core.conversion import (
    DEFAULT_VALUE_CONVERTER_REGISTRY,
    FieldValueConverterSet,
)
from pyrsql.orms.sqlalchemy.coercion import SQLAlchemyValueCoercer
from pyrsql.orms.sqlalchemy.errors import SQLAlchemyORMError


class ExampleModel:
    """Simple model marker used for field-scoped coercion tests."""


@pytest.fixture(name="coercer")
def coercer_fixture() -> SQLAlchemyValueCoercer:
    """Provides a coercer using the shared default registry."""
    return SQLAlchemyValueCoercer(registry=DEFAULT_VALUE_CONVERTER_REGISTRY)


def test_value_coercer_uses_registry_for_json_container_types(
    coercer: SQLAlchemyValueCoercer,
) -> None:
    """Coerces JSON strings through the shared registry."""
    assert coercer.coerce('["rg","cpf"]', list) == ["rg", "cpf"]


def test_value_coercer_uses_field_specific_converter_first(
    coercer: SQLAlchemyValueCoercer,
) -> None:
    """Prefers field-scoped converters over the generic registry."""
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


def test_value_coercer_wraps_field_converter_errors(
    coercer: SQLAlchemyValueCoercer,
) -> None:
    """Raises ORM errors with field context for field-scoped failures."""
    field_converters = FieldValueConverterSet(
        field_converters={},
        model_field_converters={ExampleModel: {"aliases": int}},
    )

    with pytest.raises(
        SQLAlchemyORMError,
        match=r"Failed to convert 'abc' for field 'aliases'\.",
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
