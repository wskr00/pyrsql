"""SQLAlchemy backend-specific exceptions."""


class SQLAlchemyBackendError(ValueError):
    """Base exception for SQLAlchemy backend failures."""


class SQLAlchemyModelInspectionError(SQLAlchemyBackendError):
    """Raised when a model cannot be inspected as a mapped class."""


class SQLAlchemyPathResolutionError(SQLAlchemyBackendError):
    """Raised when a semantic field path cannot be resolved."""
