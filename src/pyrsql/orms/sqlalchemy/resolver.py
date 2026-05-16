"""Path resolution for SQLAlchemy ORM models."""

from __future__ import annotations

from threading import RLock
from typing import TYPE_CHECKING, Any, Final, cast

from pyrsql.core.joins import JoinHint
from pyrsql.core.json.path import JSONPath
from pyrsql.orms.sqlalchemy.errors import (
    SQLAlchemyORMError,
    SQLAlchemyPathResolutionError,
)
from pyrsql.orms.sqlalchemy.introspection import SQLAlchemyModelInspector
from pyrsql.orms.sqlalchemy.types import (
    SQLAlchemyAttributeKind,
    SQLAlchemyJoinPlan,
    SQLAlchemyResolvedPath,
)

if TYPE_CHECKING:
    from sqlalchemy.sql.elements import ColumnElement

    from pyrsql.core.field_policy import FieldPolicySet
    from pyrsql.orms.sqlalchemy.types import (
        SQLAlchemyMappedAttribute,
    )

_MAX_FIELD_MAPPING_EXPANSIONS: Final = 32


class SQLAlchemyPathResolver:
    """Resolves bound field paths into ORM joins and leaf attributes."""

    __slots__ = ("_cache_lock", "_default_resolution_cache", "_inspector")

    def __init__(
        self,
        *,
        inspector: SQLAlchemyModelInspector | None = None,
    ) -> None:
        """Initializes the resolver with an optional shared inspector."""
        self._cache_lock = RLock()
        self._inspector = inspector or SQLAlchemyModelInspector()
        self._default_resolution_cache: dict[
            tuple[type[Any], str],
            SQLAlchemyResolvedPath,
        ] = {}

    def resolve(
        self,
        model: type[Any],
        field_path: str,
        *,
        field_policy: FieldPolicySet | None = None,
    ) -> SQLAlchemyResolvedPath:
        """Resolves a dotted field path against a mapped SQLAlchemy model.

        Returns:
            The resolved SQLAlchemy path.
        """
        if field_policy is None or field_policy.is_empty:
            with self._cache_lock:
                cache_key = (model, field_path)
                cached_path = self._default_resolution_cache.get(cache_key)
                if cached_path is not None:
                    return cached_path
                resolved_path = self._resolve_with_field_policy(
                    model,
                    field_path,
                    field_policy=None,
                )
                self._default_resolution_cache[cache_key] = resolved_path
                return resolved_path
        return self._resolve_with_field_policy(
            model,
            field_path,
            field_policy=field_policy,
        )

    def _resolve_with_field_policy(
        self,
        model: type[Any],
        field_path: str,
        *,
        field_policy: FieldPolicySet | None,
    ) -> SQLAlchemyResolvedPath:
        """Resolves a dotted field path with the provided field policy.

        Returns:
            The resolved SQLAlchemy path.

        Raises:
            SQLAlchemyPathResolutionError: If the field path or mapped fields
                are invalid.
            SQLAlchemyORMError: If SQLAlchemy metadata resolution fails.
        """
        if not field_path:
            raise SQLAlchemyPathResolutionError("Field path cannot be empty.")

        raw_segments = tuple(field_path.split("."))
        if not raw_segments or any(not segment for segment in raw_segments):
            raise SQLAlchemyPathResolutionError(
                f"Field path {field_path!r} is invalid.",
            )
        segments = raw_segments

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
                    mapped_segments = tuple(mapped_segment.split("."))
                    if any(not part for part in mapped_segments):
                        raise SQLAlchemyPathResolutionError(
                            f"Mapped field {segment!r} on "
                            f"{current_model.__name__!r} is invalid.",
                        )
                    segments_to_resolve[segment_index : segment_index + 1] = (
                        mapped_segments
                    )
                    expansion_count += 1
                    if expansion_count > _MAX_FIELD_MAPPING_EXPANSIONS:
                        raise SQLAlchemyPathResolutionError(
                            "Field mapping expansion exceeded the supported "
                            "limit.",
                        )
                    continue
            mapped_attribute = self._inspector.get_mapped_attribute(
                current_model,
                segment,
            )
            is_last_segment = segment_index == len(segments_to_resolve) - 1

            match mapped_attribute.kind:
                case SQLAlchemyAttributeKind.RELATIONSHIP:
                    if is_last_segment:
                        raise SQLAlchemyPathResolutionError(
                            f"Field path {field_path!r} ends on relationship "
                            f"{segment!r}; a column-like attribute is required.",  # noqa: E501
                        )
                    joins.append(
                        SQLAlchemyJoinPlan(
                            key=self._make_join_key(current_model, segment),
                            attribute=mapped_attribute.attribute,
                            default_hint=JoinHint.INNER,
                            is_collection=mapped_attribute.is_collection,
                        ),
                    )
                    if mapped_attribute.mapper is None:
                        raise SQLAlchemyORMError(
                            "Relationship path resolution requires a mapper.",
                        )
                    current_model = mapped_attribute.mapper.class_
                    segment_index += 1
                    continue
                case SQLAlchemyAttributeKind.COLUMN:
                    if not is_last_segment:
                        if mapped_attribute.is_json:
                            return SQLAlchemyResolvedPath(
                                root_model=model,
                                leaf_model=current_model,
                                field_path=".".join(segments_to_resolve),
                                joins=tuple(joins),
                                leaf_attribute=cast(
                                    "ColumnElement[Any]",
                                    mapped_attribute.attribute,
                                ),
                                python_type=None,
                                json_path=JSONPath(
                                    segments=tuple(
                                        segments_to_resolve[
                                            segment_index + 1 :
                                        ],
                                    ),
                                ),
                                is_json=True,
                            )
                        raise SQLAlchemyPathResolutionError(
                            f"Field path {field_path!r} traverses through "
                            f"non-relationship segment {segment!r}.",
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
                case _:
                    raise SQLAlchemyORMError(
                        "Path resolution encountered an unsupported attribute "
                        f"kind {mapped_attribute.kind!r}.",
                    )

        if leaf_attribute is None:
            raise SQLAlchemyORMError(
                "Path resolution ended without a resolved leaf attribute.",
            )
        return SQLAlchemyResolvedPath(
            root_model=model,
            leaf_model=current_model,
            field_path=field_path,
            joins=tuple(joins),
            leaf_attribute=cast(
                "ColumnElement[Any]",
                leaf_attribute.attribute,
            ),
            python_type=leaf_attribute.python_type,
            json_path=JSONPath(),
            is_json=leaf_attribute.is_json,
        )

    @staticmethod
    def _make_join_key(
        model: type[Any],
        segment: str,
    ) -> str:
        """Builds the stable join-hint lookup key for one relationship step.

        Returns:
            A stable join-hint lookup key.
        """
        return f"{model.__name__}.{segment}"

    @staticmethod
    def _validate_field_policy(
        field_policy: FieldPolicySet,
        model: type[Any],
        field_name: str,
        field_path: str,
    ) -> None:
        """Validates field access using global and model-specific rules.

        Raises:
            SQLAlchemyPathResolutionError: If the field access is invalid.
        """
        try:
            field_policy.validate_global_field_access(field_path)
            field_policy.validate_model_field_access(model, field_name)
        except ValueError as error:
            raise SQLAlchemyPathResolutionError(str(error)) from error
