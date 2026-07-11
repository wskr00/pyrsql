"""Shared SQLAlchemy ORM value objects and type aliases."""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING, Any, TypeAlias

import msgspec
from sqlalchemy.orm import Mapper, QueryableAttribute
from sqlalchemy.sql import Select

from pyrsql.core.json.path import JSONPath

if TYPE_CHECKING:
    from sqlalchemy.sql.elements import ColumnElement

    from pyrsql.core.joins import JoinHint

SQLAlchemyModel: TypeAlias = type[Any]
SQLAlchemySelect: TypeAlias = Select[Any]
SQLAlchemyAttribute: TypeAlias = QueryableAttribute[Any]
SQLAlchemyMapper: TypeAlias = Mapper[Any]


class SQLAlchemyAttributeKind(Enum):
    """Kinds of ORM attributes relevant to path resolution."""

    COLUMN = auto()
    RELATIONSHIP = auto()


class SQLAlchemyJoinPlan(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
):
    """Represents one relationship join to be applied to a statement."""

    key: str
    attribute: SQLAlchemyAttribute
    default_hint: JoinHint
    is_collection: bool


class SQLAlchemyResolvedPath(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
):
    """Represents a resolved ORM path."""

    leaf_model: SQLAlchemyModel
    field_path: str
    joins: tuple[SQLAlchemyJoinPlan, ...]
    leaf_attribute: ColumnElement[Any]
    python_type: type[Any] | None
    json_path: JSONPath = msgspec.field(default_factory=JSONPath)
    is_json: bool = False


class SQLAlchemyMappedAttribute(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
):
    """Represents a single mapped attribute discovered by introspection."""

    name: str
    kind: SQLAlchemyAttributeKind
    attribute: SQLAlchemyAttribute
    mapper: SQLAlchemyMapper | None
    python_type: type[Any] | None
    is_collection: bool = False
    is_json: bool = False
