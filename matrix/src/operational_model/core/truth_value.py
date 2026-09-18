"""Truth value enumeration for facts."""

from __future__ import annotations

from enum import Enum


class TruthValue(str, Enum):
    """Enumerates supported truth values for facts."""

    TRUE = "true"
    FALSE = "false"
    UNKNOWN = "\u2205"
