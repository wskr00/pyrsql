"""Unit tests for the shared selector parser."""

from pyrsql.selector.parser import SelectorParser


def test_split_top_level_trims_and_discards_blank_fragments() -> None:
    """Splits top-level fragments into normalized non-empty parts."""
    parser = SelectorParser()
    fragments = parser.split_top_level(
        "  name  | @upper[ city ] |   | #123  ",
        delimiter="|",
    )
    assert fragments == ("name", "@upper[ city ]", "#123")
