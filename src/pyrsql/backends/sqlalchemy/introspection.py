"""SQLAlchemy ORM inspection helpers."""

from typing import Any

from sqlalchemy import inspect
from sqlalchemy.exc import NoInspectionAvailable
from sqlalchemy.orm import Mapper
from sqlalchemy.orm.properties import ColumnProperty

from pyrsql.backends.sqlalchemy.errors import SQLAlchemyModelInspectionError
from pyrsql.backends.sqlalchemy.types import SQLAlchemyAttributeKind
from pyrsql.backends.sqlalchemy.types import SQLAlchemyMappedAttribute


class SQLAlchemyModelInspector:
    """Provides stable access to public SQLAlchemy ORM inspection APIs."""

    def inspect_model(self, model: type[Any]) -> Mapper[Any]:
        """Returns the ORM mapper for a mapped class."""
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
        return mapper

    def get_mapped_attribute(
        self,
        model: type[Any],
        attribute_name: str,
    ) -> SQLAlchemyMappedAttribute:
        """Returns metadata for a mapped attribute by name."""
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
            )
        raise SQLAlchemyModelInspectionError(
            f"Attribute {attribute_name!r} is not mapped on model "
            f"{model.__name__!r}."
        )

    def _resolve_column_python_type(
        self,
        column_property: ColumnProperty[Any],
    ) -> type[Any] | None:
        """Returns the Python type for a column property when available."""
        if not column_property.columns:
            return None
        try:
            return column_property.columns[0].type.python_type
        except (AttributeError, NotImplementedError):
            return None
