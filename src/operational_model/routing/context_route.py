"""Routing edge definition between semantic nodes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core.route_target_kind import RouteTargetKind


@dataclass
class ContextRoute:
    """Represents a directed route from one context to another node."""

    source_context_id: str
    target_kind: RouteTargetKind
    target_id: str
    relation_id: str = "routes_to"
    metadata: dict[str, Any] = field(default_factory=dict)
