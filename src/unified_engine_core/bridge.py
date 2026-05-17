"""Bridge definition for routing between unified contexts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Bridge:
    """Connects objects across two contexts in the unified engine."""

    name: str
    from_context: str
    to_context: str
    from_objects: list[str]
    to_objects: list[str]
    relation: str = "has_relation"
