"""Backend-neutral join hint definitions."""

from enum import Enum


class JoinHint(Enum):
    """Supported backend-neutral join hint kinds."""

    INNER = "inner"
    LEFT = "left"
    RIGHT = "right"

