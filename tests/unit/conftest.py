"""Shared pytest behavior for all unit tests."""

from __future__ import annotations

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Marks every collected unit test with the shared unit marker."""
    unit_marker = pytest.mark.unit
    for item in items:
        item.add_marker(unit_marker)
