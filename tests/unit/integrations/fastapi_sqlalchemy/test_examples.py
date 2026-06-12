"""Tests for FastAPI + SQLAlchemy OpenAPI example generation."""

from __future__ import annotations

from enum import IntEnum

from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase

from pyrsql.adapters.fastapi import FastAPICriteriaConfig
from pyrsql.core.options import QueryOptions
from pyrsql.integrations.fastapi import FastAPISQLAlchemyIntegration
from pyrsql.integrations.fastapi.sqlalchemy.examples import (
    build_filter_examples,
    filter_example_value,
)


class Base(DeclarativeBase):
    """Base model for example-generation tests."""


class ExampleModel(Base):
    """Mapped model with representative scalar field types."""

    __tablename__ = "example_models"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False)
    birthday = Column(Date, nullable=False)
    created_at = Column(DateTime, nullable=False)


class Status(IntEnum):
    """Integer-backed enum used to validate example generation."""

    ACTIVE = 7


def test_build_filter_examples_uses_resolved_python_types() -> None:
    """Generates filter examples from resolved SQLAlchemy field types."""
    assert (
        build_filter_examples(ExampleModel, {"id"})["filter_by_id"]["value"]
        == "id==1"
    )
    assert (
        build_filter_examples(ExampleModel, {"name"})["filter_by_name"][
            "value"
        ]
        == "name==demo"
    )
    assert (
        build_filter_examples(
            ExampleModel,
            {"is_active"},
        )["filter_by_is_active"]["value"]
        == "is_active==true"
    )
    assert (
        build_filter_examples(
            ExampleModel,
            {"birthday"},
        )["filter_by_birthday"]["value"]
        == "birthday==2026-01-01"
    )
    assert (
        build_filter_examples(
            ExampleModel,
            {"created_at"},
        )["filter_by_created_at"]["value"]
        == "created_at==2026-01-01T10:30:00"
    )


def test_resource_generates_filter_examples_for_field_aliases() -> None:
    """Resolves example types through configured field aliases."""
    integration = FastAPISQLAlchemyIntegration(
        criteria_config=FastAPICriteriaConfig(
            query_options=QueryOptions(field_mapping={"public_id": "id"}),
        ),
    )

    resource = integration.resource(
        ExampleModel,
        filterable_fields={"public_id"},
    )

    assert (
        resource.criteria_config.filter_openapi_examples[
            "filter_by_public_id"
        ]["value"]
        == "public_id==1"
    )


def test_filter_example_value_prefers_enum_values_over_int_fallback() -> None:
    """Uses the enum member value for IntEnum types."""
    assert filter_example_value(Status) == "7"
