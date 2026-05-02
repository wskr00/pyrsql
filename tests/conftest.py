"""Shared pytest configuration for the pyrsql test suite."""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Adds project-specific pytest command-line options."""
    parser.addoption(
        "--run-performance",
        action="store_true",
        default=False,
        help="Run performance tests.",
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Skips performance tests unless they are requested explicitly."""
    if config.getoption("--run-performance"):
        return

    skip_performance = pytest.mark.skip(
        reason="use --run-performance to execute performance tests",
    )
    for item in items:
        if "performance" in item.keywords:
            item.add_marker(skip_performance)
