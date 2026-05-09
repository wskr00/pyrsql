"""SQLAlchemy ORM inspection helpers."""

from typing import Any

from sqlalchemy import inspect
from sqlalchemy.exc import NoInspectionAvailable
from sqlalchemy.orm import Mapper
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.sql.sqltypes import JSON

from pyrsql.orms.sqlalchemy.errors import SQLAlchemyModelInspectionError
from pyrsql.orms.sqlalchemy.types import (
    SQLAlchemyAttributeKind,
    SQLAlchemyMappedAttribute,
)


class SQLAlchemyModelInspector:
    """Provides stable access to public SQLAlchemy ORM inspection APIs."""

    __slots__ = ("_mapper_cache", "_attribute_cache")

    def __init__(self) -> None:
        self._mapper_cache: dict[type[Any], Mapper[Any]] = {}
        self._attribute_cache: dict[
            tuple[type[Any], str], SQLAlchemyMappedAttribute
        ] = {}

    def inspect_model(self, model: type[Any]) -> Mapper[Any]:
        """Returns the ORM mapper for a mapped class."""
        cached_mapper = self._mapper_cache.get(model)
        if cached_mapper is not None:
            return cached_mapper
        try:
            mapper = inspect(model)
        except NoInspectionAvailable as error:
            raise SQLAlchemyModelInspectionError(
                f"Type {model!r} is not a SQLAlchemy mapped class."
            ) from error
        if not isinstance(mapper, Mapper):
            raise SQLAlchemyModelInspectionError(
                f"Type {model!r} did not resolve to a SQLAlchemy ORM mapper."
            )
        self._mapper_cache[model] = mapper
        return mapper

    def get_mapped_attribute(
        self,
        model: type[Any],
        attribute_name: str,
    ) -> SQLAlchemyMappedAttribute:
        """Returns metadata for a mapped attribute by name."""
        cache_key = (model, attribute_name)
        cached_attribute = self._attribute_cache.get(cache_key)
        if cached_attribute is not None:
            return cached_attribute

        mapper = self.inspect_model(model)
        if attribute_name in mapper.relationships:
            relationship = mapper.relationships[attribute_name]
            return self._cache_mapped_attribute(
                cache_key,
                SQLAlchemyMappedAttribute(
                    name=attribute_name,
                    kind=SQLAlchemyAttributeKind.RELATIONSHIP,
                    owner_model=model,
                    attribute=getattr(model, attribute_name),
                    mapper=relationship.mapper,
                    python_type=relationship.mapper.class_,
                    is_collection=bool(relationship.uselist),
                ),
            )
        if attribute_name in mapper.column_attrs:
            column_property = mapper.column_attrs[attribute_name]
            return self._cache_mapped_attribute(
                cache_key,
                SQLAlchemyMappedAttribute(
                    name=attribute_name,
                    kind=SQLAlchemyAttributeKind.COLUMN,
                    owner_model=model,
                    attribute=getattr(model, attribute_name),
                    mapper=None,
                    python_type=self._resolve_column_python_type(
                        column_property
                    ),
                    is_json=self._is_json_column(column_property),
                ),
            )
        raise SQLAlchemyModelInspectionError(
            f"Attribute {attribute_name!r} is not mapped on model "
            f"{model.__name__!r}."
        )

    def _cache_mapped_attribute(
        self,
        cache_key: tuple[type[Any], str],
        mapped_attribute: SQLAlchemyMappedAttribute,
    ) -> SQLAlchemyMappedAttribute:
        """Stores one resolved attribute in the local cache."""
        self._attribute_cache[cache_key] = mapped_attribute
        return mapped_attribute

    @staticmethod
    def _resolve_column_python_type(
        column_property: ColumnProperty[Any],
    ) -> type[Any] | None:
        """Returns the Python type for a column property when available."""
        if not column_property.columns:
            return None
        try:
            return column_property.columns[0].type.python_type
        except (AttributeError, NotImplementedError):
            return None

    @staticmethod
    def _is_json_column(
        column_property: ColumnProperty[Any],
    ) -> bool:
        """Returns whether the column property stores JSON-like data."""
        if not column_property.columns:
            return False
        return isinstance(column_property.columns[0].type, JSON)
