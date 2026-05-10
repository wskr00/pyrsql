"""Performance regression tests for lexer and parser hot paths."""

from __future__ import annotations

from timeit import timeit

import pytest

from pyrsql.parsing.lexer import Lexer
from pyrsql.parsing.parser import Parser

from .conftest import COMPLEX_QUERY, MEDIUM_QUERY

pytestmark = [pytest.mark.performance]


def test_lexer_medium_query_remains_fast() -> None:
    """Keeps medium-sized query lexing within a broad regression budget."""
    elapsed = timeit(
        lambda: tuple(Lexer(MEDIUM_QUERY).tokenize()),
        number=5000,
    )
    average_microseconds = elapsed / 5000 * 1_000_000
    assert average_microseconds < 500.0


def test_parser_complex_query_remains_fast() -> None:
    """Keeps complex query parsing within a broad regression budget."""
    elapsed = timeit(lambda: Parser(COMPLEX_QUERY).parse(), number=3000)
    average_microseconds = elapsed / 3000 * 1_000_000
    assert average_microseconds < 1_000.0
