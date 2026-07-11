"""Shared recursive parser for pyrsql selectors."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pyrsql.selector.ast import FieldSelector, FunctionSelector, LiteralSelector

if TYPE_CHECKING:
    from pyrsql.selector.ast import (
        SelectorLiteral,
        SelectorNode,
    )


class SelectorParseError(ValueError):
    """Raised when a selector expression is malformed."""


class SelectorParser:
    """Parses column, literal, and function selectors."""

    _INTEGER_PATTERN = re.compile(r"-?\d+")
    _FLOAT_PATTERN = re.compile(r"-?\d+(?:\.\d+)?")

    def parse(
        self,
        raw_selector: str,
        *,
        max_length: int,
        context: str,
    ) -> SelectorNode:
        """Parses a selector recursively.

        Returns:
            The parsed selector node.

        Raises:
            SelectorParseError: If the selector text is invalid.
        """
        normalized_selector = self._normalize_selector_text(
            raw_selector,
            max_length=max_length,
            context=context,
        )
        if normalized_selector.startswith("@"):
            return self._parse_function_selector(
                normalized_selector,
                max_length=max_length,
                context=context,
            )
        if normalized_selector.startswith("#"):
            return LiteralSelector(
                value=self._parse_literal_value(normalized_selector[1:]),
            )
        if any(not segment for segment in normalized_selector.split(".")):
            raise SelectorParseError(
                f"{context} has invalid field selector "
                f"{normalized_selector!r}: empty path segments.",
            )
        return FieldSelector(
            raw_path=normalized_selector,
        )

    @staticmethod
    def split_top_level(text: str, *, delimiter: str) -> tuple[str, ...]:
        """Splits text on a delimiter while respecting nested brackets.

        Returns:
            The top-level split fragments.

        """
        return tuple(
            part
            for part in SelectorParser._split_top_level_parts(text, delimiter)
            if part
        )

    @staticmethod
    def _split_top_level_parts(
        text: str,
        delimiter: str,
    ) -> tuple[str, ...]:
        """Splits text on a delimiter while preserving empty fragments.

        Returns:
            The normalized top-level fragments, including empty fragments.

        Raises:
            SelectorParseError: If the brackets are unbalanced.
        """
        parts: list[str] = []
        start_index = 0
        depth = 0
        for index, character in enumerate(text):
            if character == "[":
                depth += 1
            elif character == "]":
                depth -= 1
                if depth < 0:
                    raise SelectorParseError(
                        f"Selector fragment {text!r} has unbalanced brackets.",
                    )
            elif character == delimiter and depth == 0:
                parts.append(text[start_index:index].strip())
                start_index = index + 1
        if depth != 0:
            raise SelectorParseError(
                f"Selector fragment {text!r} has unbalanced brackets.",
            )
        parts.append(text[start_index:].strip())
        return tuple(parts)

    @staticmethod
    def _split_required_top_level(
        text: str,
        *,
        delimiter: str,
        context: str,
    ) -> tuple[str, ...]:
        """Splits top-level fragments while rejecting empty entries.

        Returns:
            The normalized non-empty fragments.

        Raises:
            SelectorParseError: If brackets are unbalanced or a fragment is
                empty.
        """
        parts = SelectorParser._split_top_level_parts(text, delimiter)
        if any(not part for part in parts):
            raise SelectorParseError(context)
        return parts

    @staticmethod
    def _normalize_selector_text(
        raw_selector: str,
        *,
        max_length: int,
        context: str,
    ) -> str:
        """Validates and normalizes selector parser inputs.

        Returns:
            The stripped selector text.

        Raises:
            SelectorParseError: If the selector text is empty or too long.
        """
        normalized_selector = raw_selector.strip()
        if not normalized_selector:
            raise SelectorParseError(f"{context} cannot be empty.")
        if len(normalized_selector) > max_length:
            raise SelectorParseError(
                f"{context} exceeds the maximum supported length of "
                f"{max_length}.",
            )
        return normalized_selector

    def _parse_function_selector(
        self,
        raw_selector: str,
        *,
        max_length: int,
        context: str,
    ) -> FunctionSelector:
        """Parses a function selector recursively.

        Returns:
            The parsed function selector.

        Raises:
            SelectorParseError: If the selector syntax is invalid.
        """
        argument_start = raw_selector.find("[")
        argument_end = raw_selector.rfind("]")
        if (
            argument_start <= 1
            or argument_end <= argument_start
            or argument_end != len(raw_selector) - 1
        ):
            raise SelectorParseError(
                f"{context} has invalid function selector {raw_selector!r}.",
            )
        function_name = raw_selector[1:argument_start].strip()
        if not function_name:
            raise SelectorParseError(f"{context} has empty function name.")
        arguments_text = raw_selector[argument_start + 1 : argument_end]
        if not arguments_text.strip():
            raise SelectorParseError(
                f"{context} function {function_name!r} "
                "must have at least one argument.",
            )
        argument_fragments = self._split_required_top_level(
            arguments_text,
            delimiter="|",
            context=(
                f"{context} function {function_name!r} "
                "cannot contain empty arguments."
            ),
        )
        return FunctionSelector(
            function_name=function_name,
            arguments=tuple(
                self.parse(
                    fragment,
                    max_length=max_length,
                    context=context,
                )
                for fragment in argument_fragments
            ),
        )

    def _parse_literal_value(self, raw_literal: str) -> SelectorLiteral:
        """Parses a static literal selector value.

        Returns:
            The parsed literal value.
        """
        normalized_literal = raw_literal.replace("\t", " ")
        match normalized_literal.lower():
            case "null":
                return None
            case "true":
                return True
            case "false":
                return False
            case _:
                pass
        if self._INTEGER_PATTERN.fullmatch(normalized_literal):
            return int(normalized_literal)
        if self._FLOAT_PATTERN.fullmatch(normalized_literal):
            return float(normalized_literal)
        return normalized_literal


DEFAULT_SELECTOR_PARSER = SelectorParser()
