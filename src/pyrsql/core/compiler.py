"""ORM-neutral compilation result wrapper."""

from __future__ import annotations

from typing import Protocol, TypeAlias, TypeVar

import msgspec

_TargetT = TypeVar("_TargetT")
_ModelT = TypeVar("_ModelT")


class CompiledArtifact(Protocol):
    """Structural contract for compiled ORM artifacts."""

    def apply(self, target: _TargetT, model: type[_ModelT]) -> _TargetT:
        """Applies a compiled artifact to an ORM-specific target."""


class CompilationResult(msgspec.Struct, frozen=True, gc=False, kw_only=True):
    """Wraps one ORM-specific compiled artifact.

    Attributes:
        orm_name: Name of the ORM used to produce the compilation.
        compiled: ORM-specific compiled payload implementing ``apply``.
    """

    orm_name: str
    compiled: CompiledArtifact

    def apply(self, target: _TargetT, model: type[_ModelT]) -> _TargetT:
        """Applies the compiled artifact to an ORM-specific target.

        Args:
            target: ORM-specific target to mutate.
            model: ORM model class used to resolve the compilation.

        Returns:
            The value returned by the compiled artifact application.
        """
        return self.compiled.apply(target=target, model=model)


SortCompilationResult: TypeAlias = CompilationResult
PageCompilationResult: TypeAlias = CompilationResult
