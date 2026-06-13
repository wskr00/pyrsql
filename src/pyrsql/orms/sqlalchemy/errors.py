"""SQLAlchemy ORM-specific exceptions."""

from typing import ClassVar

from pyrsql.orms.base import ORMError


class SQLAlchemyORMError(ORMError):
    """Base exception for SQLAlchemy ORM failures."""

    code: ClassVar[str] = "sqlalchemy_orm_error"


class SQLAlchemyModelInspectionError(SQLAlchemyORMError):
    """Raised when a model cannot be inspected as a mapped class."""

    code: ClassVar[str] = "sqlalchemy_model_inspection_error"


class SQLAlchemyPathResolutionError(SQLAlchemyORMError):
    """Raised when a bound field path cannot be resolved."""

    code: ClassVar[str] = "sqlalchemy_path_resolution_error"


class SQLAlchemyJSONSupportError(SQLAlchemyORMError):
    """Raised when JSON/JSONB translation cannot be completed."""

    code: ClassVar[str] = "sqlalchemy_json_support_error"
