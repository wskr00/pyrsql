"""Unit tests for SQLAlchemy path resolution."""

# pylint: disable=wrong-import-position,unsubscriptable-object

import pytest

sqlalchemy = pytest.importorskip("sqlalchemy")

from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from pyrsql.backends.sqlalchemy.errors import SQLAlchemyPathResolutionError
from pyrsql.backends.sqlalchemy.introspection import SQLAlchemyModelInspector
from pyrsql.backends.sqlalchemy.resolver import SQLAlchemyPathResolver
from pyrsql.core.field_policy import FieldPolicySet
from pyrsql.core.joins import JoinHint


class Base(DeclarativeBase):
    """Base declarative class for backend tests."""


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
    assert resolved.python_type is str
    assert resolved.leaf_model is Company


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
