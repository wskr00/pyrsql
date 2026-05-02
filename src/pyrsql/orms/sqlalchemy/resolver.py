"""Path resolution for SQLAlchemy ORM models."""

from typing import Any
from typing import cast

from sqlalchemy.sql.elements import ColumnElement

from pyrsql.orms.sqlalchemy.errors import SQLAlchemyPathResolutionError
from pyrsql.orms.sqlalchemy.introspection import SQLAlchemyModelInspector
from pyrsql.orms.sqlalchemy.types import SQLAlchemyAttributeKind
from pyrsql.orms.sqlalchemy.types import SQLAlchemyJoinPlan
from pyrsql.orms.sqlalchemy.types import SQLAlchemyMappedAttribute
from pyrsql.orms.sqlalchemy.types import SQLAlchemyResolvedPath
from pyrsql.core.field_policy import FieldPolicySet
from pyrsql.core.json.path import JSONPath
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
        *,
        field_policy: FieldPolicySet | None = None,
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
        segments_to_resolve = list(segments)
        segment_index = 0
        expansion_count = 0

        while segment_index < len(segments_to_resolve):
            segment = segments_to_resolve[segment_index]
            if field_policy is not None:
                mapped_segment = field_policy.map_model_field(
                    current_model,
                    segment,
                )
                if mapped_segment != segment:
                    mapped_segments = tuple(
                        part for part in mapped_segment.split(".") if part
                    )
                    if not mapped_segments:
                        raise SQLAlchemyPathResolutionError(
                            f"Mapped field {segment!r} on "
                            f"{current_model.__name__!r} is invalid."
                        )
                    segments_to_resolve[
                        segment_index : segment_index + 1
                    ] = mapped_segments
                    expansion_count += 1
                    if expansion_count > 32:
                        raise SQLAlchemyPathResolutionError(
                            "Field mapping expansion exceeded the supported "
                            "limit."
                        )
                    continue
            mapped_attribute = self._inspector.get_mapped_attribute(
                current_model,
                segment,
            )
            is_last_segment = segment_index == len(segments_to_resolve) - 1

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
                        is_collection=mapped_attribute.is_collection,
                    )
                )
                assert mapped_attribute.mapper is not None
                current_model = mapped_attribute.mapper.class_
                segment_index += 1
                continue

            if not is_last_segment:
                if mapped_attribute.is_json:
                    return SQLAlchemyResolvedPath(
                        root_model=model,
                        leaf_model=current_model,
                        field_path=".".join(segments_to_resolve),
                        joins=tuple(joins),
                        leaf_attribute=cast(
                            ColumnElement[Any],
                            mapped_attribute.attribute,
                        ),
                        python_type=None,
                        json_path=JSONPath(
                            tuple(
                                segments_to_resolve[segment_index + 1 :]
                            )
                        ),
                        is_json=True,
                    )
                raise SQLAlchemyPathResolutionError(
                    f"Field path {field_path!r} traverses through "
                    f"non-relationship segment {segment!r}."
                )
            leaf_attribute = mapped_attribute
            if field_policy is not None:
                self._validate_field_policy(
                    field_policy,
                    current_model,
                    leaf_attribute.name,
                    ".".join(segments_to_resolve),
                )
            segment_index += 1

        assert leaf_attribute is not None
        return SQLAlchemyResolvedPath(
            root_model=model,
            leaf_model=current_model,
            field_path=field_path,
            joins=tuple(joins),
            leaf_attribute=cast(
                ColumnElement[Any],
                leaf_attribute.attribute,
            ),
            python_type=leaf_attribute.python_type,
        )

    def _make_join_key(
        self,
        model: type[Any],
        segment: str,
    ) -> str:
        """Builds the stable join-hint lookup key for one relationship step."""
        return f"{model.__name__}.{segment}"

    def _validate_field_policy(
        self,
        field_policy: FieldPolicySet,
        model: type[Any],
        field_name: str,
        field_path: str,
    ) -> None:
        """Validates field access using global and model-specific rules."""
        try:
            field_policy.validate_global_field_access(field_path)
            field_policy.validate_model_field_access(model, field_name)
        except ValueError as error:
            raise SQLAlchemyPathResolutionError(str(error)) from error
