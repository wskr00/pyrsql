"""SQLAlchemy ORM inspection helpers."""

from __future__ import annotations

from threading import Lock
from typing import TYPE_CHECKING, Any

from sqlalchemy import inspect
from sqlalchemy.exc import NoInspectionAvailable
from sqlalchemy.orm import Mapper
from sqlalchemy.sql.sqltypes import JSON

from pyrsql.orms.sqlalchemy.errors import SQLAlchemyModelInspectionError
from pyrsql.orms.sqlalchemy.types import (
    SQLAlchemyAttributeKind,
    SQLAlchemyMappedAttribute,
)

if TYPE_CHECKING:
    from sqlalchemy.orm.properties import ColumnProperty
    from sqlalchemy.sql.elements import NamedColumn


class SQLAlchemyModelInspector:
    """Provides stable access to public SQLAlchemy ORM inspection APIs."""

    __slots__ = (
        "_attribute_cache",
        "_attribute_cache_lock",
        "_mapper_cache",
        "_mapper_cache_lock",
    )

    def __init__(self) -> None:
        """Initializes empty caches for mapped models and attributes."""
        self._mapper_cache_lock = Lock()
        self._attribute_cache_lock = Lock()
        self._mapper_cache: dict[type[Any], Mapper[Any]] = {}
        self._attribute_cache: dict[
            tuple[type[Any], str],
            SQLAlchemyMappedAttribute,
        ] = {}

    def inspect_model(self, model: type[Any]) -> Mapper[Any]:
        """Returns the ORM mapper for a mapped class.

        Returns:
            The SQLAlchemy mapper for the model.
        """
        cached_mapper = self._mapper_cache.get(model)
        if cached_mapper is not None:
            return cached_mapper
        mapper = self._inspect_model(model)
        with self._mapper_cache_lock:
            cached_mapper = self._mapper_cache.get(model)
            if cached_mapper is not None:
                return cached_mapper
            self._mapper_cache[model] = mapper
            return mapper

    def get_mapped_attribute(
        self,
        model: type[Any],
        attribute_name: str,
    ) -> SQLAlchemyMappedAttribute:
        """Returns metadata for a mapped attribute by name.

        Returns:
            Metadata for the mapped attribute.
        """
        cache_key = (model, attribute_name)
        cached_attribute = self._attribute_cache.get(cache_key)
        if cached_attribute is not None:
            return cached_attribute

        mapped_attribute = self._inspect_mapped_attribute(model, attribute_name)
        with self._attribute_cache_lock:
            cached_attribute = self._attribute_cache.get(cache_key)
            if cached_attribute is not None:
                return cached_attribute
            self._attribute_cache[cache_key] = mapped_attribute
            return mapped_attribute

    @staticmethod
    def _inspect_model(model: type[Any]) -> Mapper[Any]:
        """Resolves one mapper through SQLAlchemy inspection APIs.

        Returns:
            The SQLAlchemy mapper for the model.

        Raises:
            SQLAlchemyModelInspectionError: If the model is not mapped.
        """
        try:
            mapper = inspect(model)
        except NoInspectionAvailable as error:
            raise SQLAlchemyModelInspectionError(
                f"Type {model!r} is not a SQLAlchemy mapped class.",
            ) from error
        if not isinstance(mapper, Mapper):
            raise SQLAlchemyModelInspectionError(
                f"Type {model!r} did not resolve to a SQLAlchemy ORM mapper.",
            )
        return mapper

    def _inspect_mapped_attribute(
        self,
        model: type[Any],
        attribute_name: str,
    ) -> SQLAlchemyMappedAttribute:
        """Builds metadata for one mapped attribute.

        Returns:
            Metadata for the mapped attribute.

        Raises:
            SQLAlchemyModelInspectionError: If the attribute is not mapped.
        """
        mapper = self.inspect_model(model)
        if attribute_name in mapper.relationships:
            relationship = mapper.relationships[attribute_name]
            return SQLAlchemyMappedAttribute(
                name=attribute_name,
                kind=SQLAlchemyAttributeKind.RELATIONSHIP,
                owner_model=model,
                attribute=getattr(model, attribute_name),
                mapper=relationship.mapper,
                python_type=relationship.mapper.class_,
                is_collection=bool(relationship.uselist),
            )
        if attribute_name in mapper.column_attrs:
            column_property = mapper.column_attrs[attribute_name]
            return SQLAlchemyMappedAttribute(
                name=attribute_name,
                kind=SQLAlchemyAttributeKind.COLUMN,
                owner_model=model,
                attribute=getattr(model, attribute_name),
                mapper=None,
                python_type=self._resolve_column_python_type(column_property),
                is_json=self._is_json_column(column_property),
            )
        raise SQLAlchemyModelInspectionError(
            f"Attribute {attribute_name!r} is not mapped on model "
            f"{model.__name__!r}.",
        )

    @staticmethod
    def _first_column(
        column_property: ColumnProperty[Any],
    ) -> NamedColumn[Any] | None:
        """Returns the first mapped column for a column property, if any."""
        if not column_property.columns:
            return None
        return column_property.columns[0]

    @classmethod
    def _resolve_column_python_type(
        cls,
        column_property: ColumnProperty[Any],
    ) -> type[Any] | None:
        """Returns the Python type for a column property when available.

        Returns:
            The column Python type, or ``None`` when unavailable.
        """
        column = cls._first_column(column_property)
        if column is None:
            return None
        try:
            return column.type.python_type
        except (AttributeError, NotImplementedError):
            return None

    @classmethod
    def _is_json_column(
        cls,
        column_property: ColumnProperty[Any],
    ) -> bool:
        """Returns whether the column property stores JSON-like data.

        Returns:
            ``True`` when the column property stores JSON-like data.
        """
        column = cls._first_column(column_property)
        if column is None:
            return False
        return isinstance(column.type, JSON)
