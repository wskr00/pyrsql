"""Shared field mapping and access-policy helpers."""

from dataclasses import dataclass
from typing import Any
from typing import Mapping


@dataclass(frozen=True, slots=True)
class FieldPolicySet:
    """Backend-neutral field mapping and access-policy configuration."""

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
        """Maps one selector segment for a specific model when configured."""
        mapping = self.model_field_mapping.get(model)
        if mapping is None:
            return selector
        return mapping.get(selector, selector)

    def validate_global_field_access(self, field_path: str) -> None:
        """Validates global whitelist and blacklist rules."""
        if self.field_whitelist and field_path not in self.field_whitelist:
            raise ValueError(f"Field {field_path!r} is not allowed.")
        if field_path in self.field_blacklist:
            raise ValueError(f"Field {field_path!r} is blocked.")

    def validate_model_field_access(
        self,
        model: type[Any],
        field_name: str,
    ) -> None:
        """Validates model-specific whitelist and blacklist rules."""
        whitelist = self.model_field_whitelist.get(model)
        if whitelist is not None and field_name not in whitelist:
            raise ValueError(
                f"Field {model.__name__}.{field_name} is not allowed."
            )
        blacklist = self.model_field_blacklist.get(model)
        if blacklist is not None and field_name in blacklist:
            raise ValueError(
                f"Field {model.__name__}.{field_name} is blocked."
            )
