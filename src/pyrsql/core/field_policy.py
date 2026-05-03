"""Shared field mapping and access-policy helpers."""

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class FieldPolicySet:
    """ORM-neutral field mapping and access-policy configuration.

    Attributes:
        field_mapping: Global selector-to-field mapping.
        field_whitelist: Globally allowed field paths.
        field_blacklist: Globally blocked field paths.
        model_field_mapping: Model-specific selector-to-field mappings.
        model_field_whitelist: Model-specific allowed field names.
        model_field_blacklist: Model-specific blocked field names.
    """

    @property
    def is_empty(self) -> bool:
        """Whether the policy carries no active restrictions."""
        return not any(
            (
                self.field_mapping,
                self.field_whitelist,
                self.field_blacklist,
                self.model_field_mapping,
                self.model_field_whitelist,
                self.model_field_blacklist,
            )
        )

    field_mapping: Mapping[str, str]
    field_whitelist: frozenset[str]
    field_blacklist: frozenset[str]
    model_field_mapping: Mapping[type[Any], Mapping[str, str]]
    model_field_whitelist: Mapping[type[Any], frozenset[str]]
    model_field_blacklist: Mapping[type[Any], frozenset[str]]

    def map_model_field(
        self,
        model: type[Any],
        selector: str,
    ) -> str:
        """Maps one selector segment for a specific model when configured.

        Args:
            model: ORM model used to look up a model-specific mapping.
            selector: Raw selector segment to map.

        Returns:
            The mapped selector segment, or the original value when no mapping
            is configured.
        """
        mapping = self.model_field_mapping.get(model)
        if mapping is None:
            return selector
        return mapping.get(selector, selector)

    def validate_global_field_access(self, field_path: str) -> None:
        """Validates global whitelist and blacklist rules.

        Args:
            field_path: Dotted field path to validate.

        Raises:
            ValueError: If the field path is not allowed or is blocked.
        """
        if self.field_whitelist and field_path not in self.field_whitelist:
            raise ValueError(f"Field {field_path!r} is not allowed.")
        if field_path in self.field_blacklist:
            raise ValueError(f"Field {field_path!r} is blocked.")

    def validate_model_field_access(
        self,
        model: type[Any],
        field_name: str,
    ) -> None:
        """Validates model-specific whitelist and blacklist rules.

        Args:
            model: ORM model used to look up model-specific rules.
            field_name: Field name to validate.

        Raises:
            ValueError: If the field name is not allowed or is blocked.
        """
        whitelist = self.model_field_whitelist.get(model)
        if whitelist is not None and field_name not in whitelist:
            raise ValueError(
                f"Field {model.__name__}.{field_name} is not allowed."
            )
        blacklist = self.model_field_blacklist.get(model)
        if blacklist is not None and field_name in blacklist:
            raise ValueError(f"Field {model.__name__}.{field_name} is blocked.")
