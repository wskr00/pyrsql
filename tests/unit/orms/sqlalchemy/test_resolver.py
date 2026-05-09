"""Unit tests for SQLAlchemy path resolution."""

# pylint: disable=wrong-import-position,unsubscriptable-object

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.sqlalchemy]

sqlalchemy = pytest.importorskip("sqlalchemy")

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from pyrsql.core.field_policy import FieldPolicySet
from pyrsql.core.joins import JoinHint
from pyrsql.core.json.path import JSONPath
from pyrsql.orms.sqlalchemy.errors import SQLAlchemyPathResolutionError
from pyrsql.orms.sqlalchemy.introspection import SQLAlchemyModelInspector
from pyrsql.orms.sqlalchemy.resolver import SQLAlchemyPathResolver


class Base(DeclarativeBase):
    """Base declarative class for ORM tests."""


class Company(Base):
    """Test company model."""

    __tablename__ = "company"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))


class User(Base):
    """Test user model."""

    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"))
    company: Mapped[Company] = relationship()
    addresses: Mapped[list["Address"]] = relationship(back_populates="user")


class Address(Base):
    """Test address model for collection relationships."""

    __tablename__ = "address"

    id: Mapped[int] = mapped_column(primary_key=True)
    city: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    user: Mapped[User] = relationship(back_populates="addresses")


class Event(Base):
    """Test event model with JSON content."""

    __tablename__ = "event"

    id: Mapped[int] = mapped_column(primary_key=True)
    payload: Mapped[dict[str, object]] = mapped_column(postgresql.JSONB)


def test_model_inspector_reads_column_metadata() -> None:
    """Inspects a mapped column attribute."""
    inspector = SQLAlchemyModelInspector()
    mapped_attribute = inspector.get_mapped_attribute(User, "name")
    assert mapped_attribute.name == "name"
    assert mapped_attribute.python_type is str
    assert mapped_attribute.mapper is None


def test_model_inspector_reads_relationship_metadata() -> None:
    """Inspects a mapped relationship attribute."""
    inspector = SQLAlchemyModelInspector()
    mapped_attribute = inspector.get_mapped_attribute(User, "company")
    assert mapped_attribute.name == "company"
    assert mapped_attribute.python_type is Company
    assert mapped_attribute.mapper is not None
    assert mapped_attribute.mapper.class_ is Company


def test_model_inspector_marks_collection_relationships() -> None:
    """Inspects whether a relationship is collection-based."""
    inspector = SQLAlchemyModelInspector()
    mapped_attribute = inspector.get_mapped_attribute(User, "addresses")
    assert mapped_attribute.is_collection is True
    assert mapped_attribute.mapper is not None
    assert mapped_attribute.mapper.class_ is Address


def test_path_resolver_resolves_direct_column() -> None:
    """Resolves a direct column path without joins."""
    resolver = SQLAlchemyPathResolver()
    resolved = resolver.resolve(User, "name")
    assert resolved.field_path == "name"
    assert not resolved.joins
    assert resolved.python_type is str
    assert resolved.leaf_model is User


def test_path_resolver_resolves_relationship_path() -> None:
    """Resolves a path that requires a relationship join."""
    resolver = SQLAlchemyPathResolver()
    resolved = resolver.resolve(User, "company.name")
    assert len(resolved.joins) == 1
    assert resolved.joins[0].attribute is User.company
    assert resolved.joins[0].key == "User.company"
    assert resolved.joins[0].default_hint is JoinHint.INNER
    assert resolved.joins[0].is_collection is False
    assert resolved.python_type is str
    assert resolved.leaf_model is Company


def test_path_resolver_marks_collection_relationship_joins() -> None:
    """Resolves collection relationships with collection metadata."""
    resolver = SQLAlchemyPathResolver()
    resolved = resolver.resolve(User, "addresses.city")
    assert len(resolved.joins) == 1
    assert resolved.joins[0].attribute is User.addresses
    assert resolved.joins[0].is_collection is True
    assert resolved.python_type is str
    assert resolved.leaf_model is Address


def test_path_resolver_rejects_terminal_relationship() -> None:
    """Rejects a path that ends on a relationship segment."""
    resolver = SQLAlchemyPathResolver()
    with pytest.raises(SQLAlchemyPathResolutionError):
        resolver.resolve(User, "company")


def test_path_resolver_rejects_path_through_column() -> None:
    """Rejects traversing through a non-relationship segment."""
    resolver = SQLAlchemyPathResolver()
    with pytest.raises(SQLAlchemyPathResolutionError):
        resolver.resolve(User, "name.value")


def test_path_resolver_applies_model_field_mapping() -> None:
    """Resolves per-model field aliases during path traversal."""
    resolver = SQLAlchemyPathResolver()
    resolved = resolver.resolve(
        User,
        "company.companyName",
        field_policy=FieldPolicySet(
            field_mapping={},
            field_whitelist=frozenset(),
            field_blacklist=frozenset(),
            model_field_mapping={Company: {"companyName": "name"}},
            model_field_whitelist={},
            model_field_blacklist={},
        ),
    )
    assert resolved.python_type is str
    assert resolved.leaf_model is Company


def test_path_resolver_enforces_model_field_whitelist() -> None:
    """Rejects leaf attributes outside model-specific whitelists."""
    resolver = SQLAlchemyPathResolver()
    with pytest.raises(SQLAlchemyPathResolutionError):
        resolver.resolve(
            User,
            "company.name",
            field_policy=FieldPolicySet(
                field_mapping={},
                field_whitelist=frozenset(),
                field_blacklist=frozenset(),
                model_field_mapping={},
                model_field_whitelist={Company: frozenset({"id"})},
                model_field_blacklist={},
            ),
        )


def test_path_resolver_resolves_json_path() -> None:
    """Resolves nested JSON paths from a JSONB column."""
    resolver = SQLAlchemyPathResolver()
    resolved = resolver.resolve(Event, "payload.user.id")
    assert resolved.is_json is True
    assert resolved.json_path == JSONPath(segments=("user", "id"))
    assert resolved.leaf_model is Event
