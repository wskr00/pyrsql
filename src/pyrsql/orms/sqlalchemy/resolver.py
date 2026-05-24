"""Path resolution for SQLAlchemy ORM models."""

from __future__ import annotations

from threading import Lock
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
_ROOT_JSON_PATH: Final = JSONPath()


class SQLAlchemyPathResolver:
    """Resolves bound field paths into ORM joins and leaf attributes."""

    __slots__ = ("_cache_lock", "_default_resolution_cache", "_inspector")

    def __init__(
        self,
        *,
        inspector: SQLAlchemyModelInspector | None = None,
    ) -> None:
        """Initializes the resolver with an optional shared inspector."""
        self._cache_lock = Lock()
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
            cache_key = (model, field_path)
            cached_path = self._default_resolution_cache.get(cache_key)
            if cached_path is not None:
                return cached_path
            with self._cache_lock:
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
        if field_policy is not None:
            self._validate_global_field_policy(field_policy, field_path)
        current_model = model
        joins: list[SQLAlchemyJoinPlan] = []
        leaf_attribute: SQLAlchemyMappedAttribute | None = None
        segments_to_resolve = list(raw_segments)
        segment_index = 0
        expansion_count = 0

        while segment_index < len(segments_to_resolve):
            segment = segments_to_resolve[segment_index]
            if field_policy is not None and self._expand_mapped_segments(
                field_policy,
                current_model,
                segment,
                segments_to_resolve,
                segment_index,
            ):
                expansion_count += 1
                if expansion_count > _MAX_FIELD_MAPPING_EXPANSIONS:
                    raise SQLAlchemyPathResolutionError(
                        "Field mapping expansion exceeded the supported limit.",
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
                            if field_policy is not None:
                                self._validate_model_field_policy(
                                    field_policy,
                                    current_model,
                                    mapped_attribute.name,
                                )
                            return self._build_resolved_path(
                                root_model=model,
                                leaf_model=current_model,
                                field_path=field_path,
                                joins=joins,
                                leaf_attribute=mapped_attribute,
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
                        self._validate_model_field_policy(
                            field_policy,
                            current_model,
                            leaf_attribute.name,
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
        return self._build_resolved_path(
            root_model=model,
            leaf_model=current_model,
            field_path=field_path,
            joins=joins,
            leaf_attribute=leaf_attribute,
            python_type=leaf_attribute.python_type,
            is_json=leaf_attribute.is_json,
        )

    @staticmethod
    def _expand_mapped_segments(
        field_policy: FieldPolicySet,
        model: type[Any],
        segment: str,
        segments_to_resolve: list[str],
        segment_index: int,
    ) -> bool:
        """Expands one model-scoped field mapping in place when configured.

        Returns:
            ``True`` when the current segment was replaced by mapped segments.

        Raises:
            SQLAlchemyPathResolutionError: If the mapped segments are invalid.
        """
        mapped_segment = field_policy.map_model_field(model, segment)
        if mapped_segment == segment:
            return False
        mapped_segments = tuple(mapped_segment.split("."))
        if any(not part for part in mapped_segments):
            raise SQLAlchemyPathResolutionError(
                f"Mapped field {segment!r} on {model.__name__!r} is invalid.",
            )
        segments_to_resolve[segment_index : segment_index + 1] = mapped_segments
        return True

    @staticmethod
    def _build_resolved_path(
        *,
        root_model: type[Any],
        leaf_model: type[Any],
        field_path: str,
        joins: list[SQLAlchemyJoinPlan],
        leaf_attribute: SQLAlchemyMappedAttribute,
        python_type: type[Any] | None,
        json_path: JSONPath | None = None,
        is_json: bool = False,
    ) -> SQLAlchemyResolvedPath:
        """Builds one immutable resolved path payload.

        Returns:
            The immutable resolved path payload.
        """
        return SQLAlchemyResolvedPath(
            root_model=root_model,
            leaf_model=leaf_model,
            field_path=field_path,
            joins=tuple(joins),
            leaf_attribute=cast(
                "ColumnElement[Any]",
                leaf_attribute.attribute,
            ),
            python_type=python_type,
            json_path=json_path if json_path is not None else _ROOT_JSON_PATH,
            is_json=is_json,
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
    def _validate_global_field_policy(
        field_policy: FieldPolicySet,
        field_path: str,
    ) -> None:
        """Validates global field access rules for one requested path.

        Raises:
            SQLAlchemyPathResolutionError: If the field path is globally
                blocked or not allowed.
        """
        try:
            field_policy.validate_global_field_access(field_path)
        except ValueError as error:
            raise SQLAlchemyPathResolutionError(str(error)) from error

    @staticmethod
    def _validate_model_field_policy(
        field_policy: FieldPolicySet,
        model: type[Any],
        field_name: str,
    ) -> None:
        """Validates model-specific field access rules for one leaf field.

        Raises:
            SQLAlchemyPathResolutionError: If the leaf field is blocked or not
                allowed for the model.
        """
        try:
            field_policy.validate_model_field_access(model, field_name)
        except ValueError as error:
            raise SQLAlchemyPathResolutionError(str(error)) from error
