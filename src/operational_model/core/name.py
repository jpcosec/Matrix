"""Language-level sign representation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Name:
    """Represents a sign used to designate a thing."""

    sign: str
    namespace: str = "default"
