"""Performance regression tests for semantic binding."""

from __future__ import annotations

from timeit import timeit

import pytest

from pyrsql.core.options import QueryOptions, SortOptions
from pyrsql.parsing.parser import Parser
from pyrsql.semantic.binder import SemanticBinder
from pyrsql.sorting.binder import SortBinder
from pyrsql.sorting.parser import SortParser

from .conftest import QUERY_TEXT, SORT_TEXT

pytestmark = [pytest.mark.performance]


def test_query_semantic_binding_remains_fast() -> None:
    """Keeps semantic query binding within a broad regression budget."""
    expression = Parser(QUERY_TEXT).parse()
    binder = SemanticBinder(QueryOptions(procedure_whitelist=("upper",)))
    elapsed = timeit(lambda: binder.bind(expression), number=5000)
    average_microseconds = elapsed / 5000 * 1_000_000
    assert average_microseconds < 200.0


def test_sort_semantic_binding_remains_fast() -> None:
    """Keeps semantic sort binding within a broad regression budget."""
    fields = SortParser(SORT_TEXT).parse()
    binder = SortBinder(SortOptions(procedure_whitelist=("upper",)))
    elapsed = timeit(lambda: binder.bind(fields), number=5000)
    average_microseconds = elapsed / 5000 * 1_000_000
    assert average_microseconds < 200.0
