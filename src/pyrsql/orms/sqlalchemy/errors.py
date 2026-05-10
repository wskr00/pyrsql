"""SQLAlchemy ORM-specific exceptions."""


class SQLAlchemyORMError(ValueError):
    """Base exception for SQLAlchemy ORM failures."""


class SQLAlchemyModelInspectionError(SQLAlchemyORMError):
    """Raised when a model cannot be inspected as a mapped class."""


class SQLAlchemyPathResolutionError(SQLAlchemyORMError):
    """Raised when a bound field path cannot be resolved."""


class SQLAlchemyJSONSupportError(SQLAlchemyORMError):
    """Raised when JSON/JSONB translation cannot be completed."""
