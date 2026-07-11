"""ORM-neutral compiled artifact contract."""

from __future__ import annotations

from typing import Protocol, TypeVar

_TargetT = TypeVar("_TargetT")
_ModelT = TypeVar("_ModelT")


class CompiledArtifact(Protocol):
    """Structural contract for compiled ORM artifacts."""

    def apply(self, target: _TargetT, model: type[_ModelT]) -> _TargetT:
        """Applies a compiled artifact to an ORM-specific target."""
