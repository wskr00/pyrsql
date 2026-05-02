"""Shared SQLAlchemy backend value objects."""

from dataclasses import dataclass
from enum import Enum
from enum import auto
from typing import Any

from sqlalchemy.orm import Mapper
from sqlalchemy.orm.attributes import InstrumentedAttribute

from pyrsql.core.joins import JoinHint


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


@dataclass(frozen=True, slots=True)
class SQLAlchemyResolvedPath:
    """Represents a resolved ORM path."""

    root_model: type[Any]
    leaf_model: type[Any]
    field_path: str
    joins: tuple[SQLAlchemyJoinPlan, ...]
    leaf_attribute: InstrumentedAttribute[Any]
    python_type: type[Any] | None


@dataclass(frozen=True, slots=True)
class SQLAlchemyMappedAttribute:
    """Represents a single mapped attribute discovered by introspection."""

    name: str
    kind: SQLAlchemyAttributeKind
    owner_model: type[Any]
    attribute: InstrumentedAttribute[Any]
    mapper: Mapper[Any] | None
    python_type: type[Any] | None
