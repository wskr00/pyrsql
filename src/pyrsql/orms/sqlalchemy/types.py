"""Shared SQLAlchemy ORM value objects."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from sqlalchemy.orm import Mapper
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import ColumnElement

from pyrsql.core.joins import JoinHint
from pyrsql.core.json.path import JSONPath


class SQLAlchemyAttributeKind(Enum):
    """Kinds of ORM attributes relevant to path resolution."""

    COLUMN = auto()
    RELATIONSHIP = auto()


@dataclass(frozen=True, slots=True)
class SQLAlchemyJoinPlan:
    """Represents one relationship join to be applied to a statement."""

    key: str
    attribute: InstrumentedAttribute[Any]
    default_hint: JoinHint
    is_collection: bool


@dataclass(frozen=True, slots=True)
class SQLAlchemyResolvedPath:
    """Represents a resolved ORM path."""

    root_model: type[Any]
    leaf_model: type[Any]
    field_path: str
    joins: tuple[SQLAlchemyJoinPlan, ...]
    leaf_attribute: ColumnElement[Any]
    python_type: type[Any] | None
    json_path: JSONPath = JSONPath()
    is_json: bool = False


@dataclass(frozen=True, slots=True)
class SQLAlchemyMappedAttribute:
    """Represents a single mapped attribute discovered by introspection."""

    name: str
    kind: SQLAlchemyAttributeKind
    owner_model: type[Any]
    attribute: InstrumentedAttribute[Any]
    mapper: Mapper[Any] | None
    python_type: type[Any] | None
    is_collection: bool = False
    is_json: bool = False
