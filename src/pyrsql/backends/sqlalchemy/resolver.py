"""Path resolution for SQLAlchemy ORM models."""

from typing import Any

from pyrsql.backends.sqlalchemy.errors import SQLAlchemyPathResolutionError
from pyrsql.backends.sqlalchemy.introspection import SQLAlchemyModelInspector
from pyrsql.backends.sqlalchemy.types import SQLAlchemyAttributeKind
from pyrsql.backends.sqlalchemy.types import SQLAlchemyJoinPlan
from pyrsql.backends.sqlalchemy.types import SQLAlchemyMappedAttribute
from pyrsql.backends.sqlalchemy.types import SQLAlchemyResolvedPath
from pyrsql.core.joins import JoinHint


class SQLAlchemyPathResolver:
    """Resolves semantic field paths into ORM joins and leaf attributes."""

    def __init__(
        self,
        *,
        inspector: SQLAlchemyModelInspector | None = None,
    ) -> None:
        self._inspector = inspector or SQLAlchemyModelInspector()

    def resolve(
        self,
        model: type[Any],
        field_path: str,
    ) -> SQLAlchemyResolvedPath:
        """Resolves a dotted field path against a mapped SQLAlchemy model."""
        if not field_path:
            raise SQLAlchemyPathResolutionError(
                "Field path cannot be empty."
            )

        segments = tuple(
            segment for segment in field_path.split(".") if segment
        )
        if not segments:
            raise SQLAlchemyPathResolutionError(
                f"Field path {field_path!r} is invalid."
            )

        current_model = model
        joins: list[SQLAlchemyJoinPlan] = []
        leaf_attribute: SQLAlchemyMappedAttribute | None = None

        for index, segment in enumerate(segments):
            mapped_attribute = self._inspector.get_mapped_attribute(
                current_model,
                segment,
            )
            is_last_segment = index == len(segments) - 1

            if mapped_attribute.kind is SQLAlchemyAttributeKind.RELATIONSHIP:
                if is_last_segment:
                    raise SQLAlchemyPathResolutionError(
                        f"Field path {field_path!r} ends on relationship "
                        f"{segment!r}; a column-like attribute is required."
                    )
                joins.append(
                    SQLAlchemyJoinPlan(
                        key=self._make_join_key(current_model, segment),
                        attribute=mapped_attribute.attribute,
                        default_hint=JoinHint.INNER,
                    )
                )
                assert mapped_attribute.mapper is not None
                current_model = mapped_attribute.mapper.class_
                continue

            if not is_last_segment:
                raise SQLAlchemyPathResolutionError(
                    f"Field path {field_path!r} traverses through "
                    f"non-relationship segment {segment!r}."
                )
            leaf_attribute = mapped_attribute

        assert leaf_attribute is not None
        return SQLAlchemyResolvedPath(
            root_model=model,
            leaf_model=current_model,
            field_path=field_path,
            joins=tuple(joins),
            leaf_attribute=leaf_attribute.attribute,
            python_type=leaf_attribute.python_type,
        )

    def _make_join_key(
        self,
        model: type[Any],
        segment: str,
    ) -> str:
        """Builds the stable join-hint lookup key for one relationship step."""
        return f"{model.__name__}.{segment}"
