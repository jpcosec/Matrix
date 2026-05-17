"""Context definition for the unified engine."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Context:
    """Represents one logical context in the unified engine."""

    name: str
    objects: list[str]
    properties: list[str]
    objects_meta: dict
    properties_meta: dict
    truths: dict
