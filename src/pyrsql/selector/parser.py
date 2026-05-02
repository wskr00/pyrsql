"""Shared recursive parser for pyrsql selectors."""

import re

from pyrsql.selector import ast


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
    ) -> ast.Selector:
        """Parses a selector recursively."""
        if len(raw_selector) > max_length:
            raise SelectorParseError(
                f"{context} exceeds the maximum supported length of "
                f"{max_length}."
            )
        if raw_selector.startswith("@"):
            return self._parse_function_selector(
                raw_selector,
                max_length=max_length,
                context=context,
            )
        if raw_selector.startswith("#"):
            return ast.LiteralSelector(
                value=self._parse_literal_value(raw_selector[1:])
            )
        return ast.ColumnSelector(selector=raw_selector)

    def split_top_level(self, text: str, *, delimiter: str) -> tuple[str, ...]:
        """Splits text on a delimiter while respecting nested brackets."""
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
                        f"Selector fragment {text!r} has unbalanced brackets."
                    )
            elif character == delimiter and depth == 0:
                part = text[start_index:index].strip()
                if part:
                    parts.append(part)
                start_index = index + 1
        if depth != 0:
            raise SelectorParseError(
                f"Selector fragment {text!r} has unbalanced brackets."
            )
        final_part = text[start_index:].strip()
        if final_part:
            parts.append(final_part)
        return tuple(parts)

    def _parse_function_selector(
        self,
        raw_selector: str,
        *,
        max_length: int,
        context: str,
    ) -> ast.FunctionSelector:
        """Parses a function selector recursively."""
        argument_start = raw_selector.find("[")
        argument_end = raw_selector.rfind("]")
        if (
            argument_start <= 1
            or argument_end <= argument_start
            or argument_end != len(raw_selector) - 1
        ):
            raise SelectorParseError(
                f"{context} has invalid function selector {raw_selector!r}."
            )
        function_name = raw_selector[1:argument_start].strip()
        if not function_name:
            raise SelectorParseError(f"{context} has empty function name.")
        arguments_text = raw_selector[argument_start + 1 : argument_end]
        argument_fragments = self.split_top_level(arguments_text, delimiter="|")
        if not argument_fragments:
            raise SelectorParseError(
                f"{context} function {function_name!r} must have at least one "
                "argument."
            )
        return ast.FunctionSelector(
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

    def _parse_literal_value(self, raw_literal: str) -> ast.SelectorLiteral:
        """Parses a static literal selector value."""
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
