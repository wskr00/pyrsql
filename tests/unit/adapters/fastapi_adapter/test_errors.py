"""Unit tests for FastAPI adapter error payload helpers."""

from __future__ import annotations

from pyrsql.adapters.fastapi.errors import FastAPIAdapterErrorPayload
from pyrsql.orms.sqlalchemy.errors import SQLAlchemyPathResolutionError


def test_backend_error_payload_preserves_http_detail_shape() -> None:
    """Builds the expected HTTP detail mapping for backend errors."""
    payload = FastAPIAdapterErrorPayload.from_backend_error(
        "filter",
        error_type="query_backend_error",
        error=SQLAlchemyPathResolutionError("Field 'password' is not allowed."),
    )

    assert payload.to_http_detail() == {
        "type": "urn:pyrsql:problem:query-backend-error",
        "title": "Query backend error",
        "parameter": "filter",
        "detail": "Field 'password' is not allowed.",
        "errors": [
            {
                "code": "sqlalchemy_path_resolution_error",
                "detail": "Field 'password' is not allowed.",
                "field": "password",
                "location": None,
            },
        ],
    }
